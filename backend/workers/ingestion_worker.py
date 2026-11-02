"""
ArchiveMind - Background Ingestion Worker
Processes raw manuscript images received from Raspberry Pi or Web Uploads:
1. Image validation & SHA-256 calculation
2. CV Enhancement (deskew, bilateral filter, CLAHE)
3. OCR / HTR recognition
4. Physical condition prediction
5. Real MiniLM 384-d semantic chunk embedding
6. Atomic SQLite updates and FTS5 synchronization
"""

import os
import time
import uuid
import sqlite3
import traceback
from typing import Dict, Any, Optional

try:
    from ..services import (
        image_processing,
        ocr_service,
        htr_service,
        embedding_service,
        classification_service,
        handwriting_analysis
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from services import (
        image_processing,
        ocr_service,
        htr_service,
        embedding_service,
        classification_service,
        handwriting_analysis
    )


def process_ingestion_pipeline(
    db_path: str,
    job_id: str,
    original_image_path: str,
    scan_id: str,
    device_id: Optional[str] = None,
    document_title: Optional[str] = None,
    collection_id: int = 1,
    doc_type: str = "Manuscript",
    date_written: str = "Circa 17th Century",
    author_name: str = "Historical Manuscript Author",
    language: str = "English",
    ocr_mode: str = "auto"
) -> Dict[str, Any]:
    """
    Executes end-to-end processing synchronously in a worker thread.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        # Step A: Update job to PROCESSING
        cur.execute("""
            UPDATE ingestion_job 
            SET status = 'PROCESSING'
            WHERE job_id = ?
        """, (job_id,))
        conn.commit()

        # Step B: CV Enhancement
        storage_dir = os.path.dirname(os.path.dirname(original_image_path))
        processed_dir = os.path.join(storage_dir, "processed")
        enhancement = image_processing.enhance_manuscript(
            original_path=original_image_path,
            processed_dir=processed_dir,
            output_prefix="proc_"
        )
        enhanced_path = enhancement["processed_path"]

        # Step C: Compute SHA-256
        import hashlib
        hasher = hashlib.sha256()
        with open(original_image_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        sha256_checksum = hasher.hexdigest()

        # Step D: OCR / HTR Extraction
        if ocr_mode == "handwritten":
            text_rec = htr_service.perform_handwriting_recognition(enhanced_path, user_mode="handwritten")
        elif ocr_mode == "printed":
            text_rec = ocr_service.perform_printed_ocr(enhanced_path)
        else: # Auto
            # Run printed OCR first; if low word count, run HTR
            text_rec = ocr_service.perform_printed_ocr(enhanced_path)
            if text_rec["word_count"] < 8:
                text_rec = htr_service.perform_handwriting_recognition(enhanced_path, user_mode="auto")

        extracted_text = text_rec["raw_text"]
        ocr_confidence = text_rec["confidence"]
        ocr_engine = text_rec["engine"]
        ocr_model = text_rec["model_name"]

        # Step E: Physical Condition Classification
        condition_meta = classification_service.analyze_image_condition(enhanced_path)
        condition_label = condition_meta["predicted_label"]
        condition_conf = condition_meta["confidence"]

        # Step F: Handwriting Visual Forensics
        forensics_meta = handwriting_analysis.extract_visual_style_features(enhanced_path)

        # Step G: Create or Link Relational Document Record
        title = document_title or f"Acquired Manuscript — {scan_id}"
        
        # Check or insert Person
        cur.execute("SELECT person_id FROM person WHERE full_name = ?", (author_name,))
        person_row = cur.fetchone()
        if person_row:
            person_id = person_row["person_id"]
        else:
            cur.execute("INSERT INTO person (full_name, biography) VALUES (?, 'Archival contributor / manuscript author')", (author_name,))
            person_id = cur.lastrowid

        # Insert document record
        cur.execute("""
            INSERT INTO document (
                collection_id, digitized_by, title, doc_type, date_written,
                ocr_text_cache, checksum_value, physical_condition, language,
                image_path, ocr_status
            ) VALUES (?, 3, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED')
        """, (
            collection_id,
            title,
            doc_type,
            date_written,
            extracted_text,
            sha256_checksum,
            condition_label if condition_label in ('Pristine', 'Good', 'Fragile', 'Critical-Decay') else 'Good',
            language,
            os.path.basename(enhanced_path)
        ))
        document_id = cur.lastrowid

        # Insert document_author
        cur.execute("""
            INSERT OR IGNORE INTO document_author (document_id, person_id, attribution_type, confidence_score)
            VALUES (?, ?, 'Author', ?)
        """, (document_id, person_id, ocr_confidence))

        # Insert document_image
        cur.execute("""
            INSERT INTO document_image (
                document_id, job_id, original_path, processed_path, sha256, width, height
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            document_id,
            job_id,
            original_image_path,
            enhanced_path,
            sha256_checksum,
            enhancement["original_dimensions"]["width"],
            enhancement["original_dimensions"]["height"]
        ))
        image_id = cur.lastrowid

        # Insert ocr_result
        cur.execute("""
            INSERT INTO ocr_result (
                image_id, engine, model_name, raw_text, corrected_text, confidence
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            image_id,
            ocr_engine,
            ocr_model,
            extracted_text,
            extracted_text,
            ocr_confidence
        ))
        ocr_id = cur.lastrowid

        # Insert ML Prediction (Condition)
        cur.execute("""
            INSERT INTO ml_prediction (
                document_id, model_name, model_version, prediction_type, predicted_label, confidence
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            document_id,
            condition_meta["model_name"],
            condition_meta["model_version"],
            condition_meta["prediction_type"],
            condition_label,
            condition_conf
        ))

        # Step H: Overlapping Chunks and Real MiniLM Embeddings
        chunks = embedding_service.chunk_text(extracted_text, chunk_size=80, overlap=20)
        if not chunks:
            chunks = [extracted_text or title]

        # Generate 384-d embeddings
        embeddings = embedding_service.encode_texts(chunks)

        for idx, (chunk_str, emb_vec) in enumerate(zip(chunks, embeddings)):
            cur.execute("""
                INSERT INTO document_chunk (document_id, chunk_index, chunk_text, source_ocr_id)
                VALUES (?, ?, ?, ?)
            """, (document_id, idx, chunk_str, ocr_id))
            chunk_id = cur.lastrowid

            blob = embedding_service.vector_to_blob(emb_vec)
            cur.execute("""
                INSERT INTO chunk_embedding (chunk_id, model_name, dimensions, embedding_blob)
                VALUES (?, ?, 384, ?)
            """, (chunk_id, embedding_service.MODEL_NAME, blob))

        # Step I: Update FTS5 Index
        cur.execute("""
            INSERT INTO document_fts (document_id, title, ocr_text_cache)
            VALUES (?, ?, ?)
        """, (document_id, title, extracted_text))

        # Step J: Update Ingestion Job
        cur.execute("""
            UPDATE ingestion_job
            SET status = 'COMPLETED',
                enhanced_image_path = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE job_id = ?
        """, (enhanced_path, job_id))

        conn.commit()

        return {
            "success": True,
            "job_id": job_id,
            "document_id": document_id,
            "title": title,
            "checksum_sha256": sha256_checksum,
            "condition": condition_label,
            "condition_confidence": condition_conf,
            "ocr_text": extracted_text,
            "ocr_engine": ocr_engine,
            "chunks_count": len(chunks),
            "skew_angle": enhancement["skew_angle"],
            "enhanced_path": enhanced_path
        }

    except Exception as e:
        conn.rollback()
        err_msg = traceback.format_exc()
        cur.execute("""
            UPDATE ingestion_job
            SET status = 'FAILED',
                error_message = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE job_id = ?
        """, (str(e), job_id))
        conn.commit()
        return {"success": False, "job_id": job_id, "error": str(e), "traceback": err_msg}
    finally:
        conn.close()
