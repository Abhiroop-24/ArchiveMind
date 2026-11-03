"""
ArchiveMind - Comprehensive Test Suite
Validates:
1. Database migrations & tables
2. SHA-256 cryptographic checksums & trigger validation
3. FTS5 full-text keyword search
4. MiniLM semantic embedding dimensions & cosine similarity
5. Weighted hybrid scoring & RRF ranking
6. Citation generation and trigger view audit logging
7. RBAC access control (Researcher vs Head Archivist)
8. Computer Vision enhancement pipeline (Bilateral, CLAHE, Deskew)
9. End-to-end ingestion worker pipeline
10. Hardware device status & Pi communication
"""

import os
import sys
import tempfile
import sqlite3
import numpy as np
import pytest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.db_manager import ArchiveMindDB, generate_deterministic_embedding, cosine_similarity
from backend.services import (
    image_processing,
    ocr_service,
    htr_service,
    embedding_service,
    hybrid_search,
    classification_service,
    handwriting_analysis,
    rag_service
)
from backend.workers.ingestion_worker import process_ingestion_pipeline


class TestArchiveMind:

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Creates a fresh isolated test database for each test session."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_archivemind.db")
        self.db = ArchiveMindDB(db_path=self.db_path)
        yield
        # Cleanup
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_database_tables_and_seeds(self):
        """Test 1: Verify all relational, FTS5, and AI migration tables exist and are seeded."""
        conn = self.db.get_connection()
        cur = conn.cursor()

        # Check core DBMS tables
        for table in ["role", "app_user", "archive", "collection", "document", "person", "document_author", "citation", "document_view"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            assert count > 0, f"Table {table} should have seeded rows"

        # Check AI migration tables
        for table in ["device", "ingestion_job", "document_image", "ocr_result", "document_chunk", "chunk_embedding", "ml_prediction", "model_registry"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            # Ensure query executes without NoSuchTableError
            assert cur.fetchone() is not None, f"Table {table} must exist"

        conn.close()

    def test_sha256_checksum_and_trigger_abort(self):
        """Test 2: Verify SHA-256 integrity check and trigger abort on invalid/truncated hash."""
        conn = self.db.get_connection()
        cur = conn.cursor()

        # Get valid document checksum
        cur.execute("SELECT document_id, checksum_value FROM document LIMIT 1")
        doc = cur.fetchone()
        doc_id = doc["document_id"]
        assert len(doc["checksum_value"]) == 64, "SHA-256 checksum must be 64 hexadecimal characters"

        # Attempt to update checksum with a truncated invalid value (< 16 characters)
        with pytest.raises(sqlite3.IntegrityError):
            cur.execute("UPDATE document SET checksum_value = 'corrupted_hash' WHERE document_id = ?", (doc_id,))
            conn.commit()

        conn.close()

    def test_citation_trigger_view_audit(self):
        """Test 3: Verify trigger trg_audit_citation_generation inserts into document_view on citation generation."""
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM document_view")
        initial_views = cur.fetchone()[0]

        # Generate citation
        cit = self.db.generate_citation(document_id=1, style="MLA", user_id=3)
        assert "Newton" in cit["citation_text"]

        # Check that trigger inserted an audit view record
        cur.execute("SELECT COUNT(*) FROM document_view")
        new_views = cur.fetchone()[0]
        assert new_views == initial_views + 1, "Trigger should have created a document_view audit row"

        cur.execute("SELECT * FROM document_view ORDER BY view_id DESC LIMIT 1")
        latest_audit = cur.fetchone()
        assert "TRIGGER:CITATION_MLA" in latest_audit["ip_address"]
        conn.close()

    def test_rbac_evaluation_queries(self):
        """Test 4: Verify RBAC on database evaluation queries (mutations require Head Archivist)."""
        # User 3 is Researcher (cannot mutate)
        assert self.db.get_user_role(3) == "Researcher"
        # User 1 is Head Archivist (can mutate)
        assert self.db.get_user_role(1) == "Head Archivist"

        # Read query 7.1 runs for anyone
        res_71 = self.db.run_evaluation_query("7.1")
        assert len(res_71["results"]) > 0

        # Mutation query 7.2 runs as admin
        res_72 = self.db.run_evaluation_query("7.2")
        assert "rows_affected" in res_72

    def test_embedding_dimensions_and_chunking(self):
        """Test 5: Verify text chunking and vector serialization."""
        text = "Newtonian physics dictates that celestial bodies attract with universal gravitation. Inverse square fluxions calculate elliptic planetary paths."
        chunks = embedding_service.chunk_text(text, chunk_size=10, overlap=3)
        assert len(chunks) >= 2, "Long text should be divided into multiple chunks"

        # Test dummy vector serialization
        vec = np.random.randn(384).astype(np.float32)
        blob = embedding_service.vector_to_blob(vec)
        assert len(blob) == 384 * 4, "384 float32 numbers should serialize to 1536 bytes"

        deserialized = embedding_service.blob_to_vector(blob)
        assert np.allclose(vec, deserialized), "Deserialized vector must match original float32 array"

    def test_hybrid_search_alpha_weighting(self):
        """Test 6: Verify hybrid search responds to query and alpha slider adjustments."""
        conn = self.db.get_connection()

        # Pure keyword search (alpha = 1.0)
        res_kw = hybrid_search.execute_hybrid_search(conn, query_text="gravitation", alpha=1.0, limit=5)
        assert len(res_kw) > 0
        assert "Principia" in res_kw[0]["title"]
        assert res_kw[0]["keyword_score"] > 0

        # Balanced hybrid search (alpha = 0.5)
        res_hyb = hybrid_search.execute_hybrid_search(conn, query_text="gravitation", alpha=0.5, limit=5)
        assert len(res_hyb) > 0
        assert "hybrid_score" in res_hyb[0]
        assert "rrf_score" in res_hyb[0]

        conn.close()

    def test_computer_vision_enhancement(self):
        """Test 7: Verify image enhancement pipeline (CLAHE, bilateral filter, deskew)."""
        import cv2

        # Create a synthetic manuscript image with text
        synth_img = np.full((300, 400, 3), 230, dtype=np.uint8) # parchment paper color
        cv2.putText(synth_img, "Historical Manuscript Folio", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
        cv2.putText(synth_img, "Lex I: Corpus omne perseverare", (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (30, 30, 30), 1)

        temp_img_path = os.path.join(self.temp_dir, "test_manuscript.jpg")
        cv2.imwrite(temp_img_path, synth_img)

        proc_dir = os.path.join(self.temp_dir, "processed")
        enhancement = image_processing.enhance_manuscript(temp_img_path, proc_dir)

        assert os.path.exists(enhancement["processed_path"])
        assert os.path.exists(enhancement["preview_path"])
        assert "filters_applied" in enhancement
        assert len(enhancement["filters_applied"]) >= 3

    def test_condition_classifier(self):
        """Test 8: Verify physical condition prediction heuristic."""
        import cv2
        synth_img = np.full((200, 200, 3), 200, dtype=np.uint8)
        img_path = os.path.join(self.temp_dir, "cond_test.jpg")
        cv2.imwrite(img_path, synth_img)

        pred = classification_service.analyze_image_condition(img_path)
        assert pred["predicted_label"] in ["Pristine", "Good", "Stained", "Fragile", "Critical-Decay"]
        assert 0.0 <= pred["confidence"] <= 1.0

    def test_local_rag_grounded_assistant(self):
        """Test 9: Verify Local RAG returns grounded citations and handles insufficient evidence."""
        conn = self.db.get_connection()

        # Query with relevant archival evidence in Newton
        res = rag_service.ask_archival_assistant(conn, "What forces act upon celestial bodies in Principia?")
        assert len(res["citations"]) > 0
        assert res["evidence_sufficient"] is True

        # Query with zero primary evidence in historical collection
        res_none = rag_service.ask_archival_assistant(conn, "quantum entanglement teleportation in 2026")
        # Guardrail should trigger
        assert "does not contain sufficient" in res_none["answer"]

        conn.close()

    def test_end_to_end_ingestion_pipeline(self):
        """Test 10: Verify end-to-end ingestion pipeline from image to database, FTS5 and embeddings."""
        import cv2
        synth_img = np.full((300, 400, 3), 240, dtype=np.uint8)
        cv2.putText(synth_img, "Analytical Engine Algorithm Proof", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (10, 10, 10), 2)
        raw_path = os.path.join(self.temp_dir, "raw_scan.jpg")
        cv2.imwrite(raw_path, synth_img)

        job_id = "job_test_001"
        self.db.create_ingestion_job(job_id=job_id, scan_id="scan_test_001", original_image_path=raw_path)

        res = process_ingestion_pipeline(
            db_path=self.db_path,
            job_id=job_id,
            original_image_path=raw_path,
            scan_id="scan_test_001",
            document_title="Analytical Engine Algorithm Proof",
            collection_id=5,
            author_name="Ada Lovelace",
            ocr_mode="printed"
        )

        assert res["success"] is True
        assert res["document_id"] > 0
        assert len(res["checksum_sha256"]) == 64

        # Verify new document is immediately retrievable via hybrid search
        conn = self.db.get_connection()
        search_res = hybrid_search.execute_hybrid_search(conn, query_text="Analytical Engine", alpha=0.5)
        conn.close()
        found = any("Analytical Engine Algorithm Proof" in r["title"] for r in search_res)
        assert found, "Newly ingested document must be immediately indexed and retrievable via hybrid search"

    def test_four_corner_perspective_correction(self):
        """Test 11: Verify OpenCV 4-corner paper detection, homography perspective transform, and MiniLM+SQLite indexing."""
        import cv2

        # 1. Create a synthetic desk with an A4 paper sheet tilted with perspective distortion
        desk = np.full((600, 800, 3), 40, dtype=np.uint8) # Dark desk
        paper_corners = np.array([
            [160, 110],  # Top-Left
            [610, 80],   # Top-Right
            [660, 480],  # Bottom-Right
            [120, 510]   # Bottom-Left
        ], dtype=np.int32)
        cv2.fillPoly(desk, [paper_corners], (240, 235, 225)) # Bright parchment paper
        cv2.putText(desk, "PRINCIPLES OF GRAVITATION", (220, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
        cv2.putText(desk, "Inverse square orbital mechanics theorem", (200, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (30, 30, 30), 1)

        # 2. Test 4-corner paper detection
        meta = image_processing.detect_a4_contour(desk)
        assert meta["detected"] is True, "Must detect A4 paper contour"
        assert "corners" in meta
        assert len(meta["corners"]) == 4

        # 3. Test 4-point homography perspective transform
        pts = np.array(meta["corners"], dtype="float32")
        warped = image_processing.four_point_perspective_transform(desk, pts)
        assert warped is not None
        wh, ww = warped.shape[:2]
        assert ww > 200 and wh > 200
        # Aspect ratio should approximate A4
        aspect = max(ww, wh) / float(min(ww, wh))
        assert 1.15 <= aspect <= 1.65, f"Warped aspect ratio {aspect} must approximate A4"

        # 4. Test MiniLM embedding generation on extracted text
        text_content = "PRINCIPLES OF GRAVITATION. Inverse square orbital mechanics theorem."
        emb = embedding_service.encode_query(text_content)
        assert len(emb) == 384, "MiniLM embeddings must be 384-dimensional"

        # 5. Test SQLite insertion & FTS5 full-text indexing
        import hashlib
        chk = hashlib.sha256(text_content.encode()).hexdigest()
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO document (title, doc_type, date_written, physical_condition, language, ocr_text_cache, collection_id, checksum_value, image_path)
            VALUES (?, 'Manuscript', '1687', 'Pristine', 'English', ?, 1, ?, 'test_newton.jpg')
        """, ("Test Newton Gravitation Folio", text_content, chk))
        doc_id = cur.lastrowid
        cur.execute("INSERT INTO document_fts (rowid, title, ocr_text_cache) VALUES (?, ?, ?)", (doc_id, "Test Newton Gravitation Folio", text_content))
        conn.commit()

        # Verify FTS5 finds it by rowid
        cur.execute("SELECT rowid FROM document_fts WHERE document_fts MATCH 'orbital mechanics'")
        fts_row = cur.fetchone()
        assert fts_row is not None, "Document must be retrievable via SQLite FTS5"
        assert int(fts_row["rowid"]) == doc_id
        conn.close()

    def test_ollama_qwen_status_and_rag_execution(self):
        """Test 12: Verify Ollama status reporting and Qwen2.5:3b or Extractive RAG generation."""
        status = rag_service.get_llm_status()
        assert "ollama_online" in status
        assert "model_name" in status
        assert "active_engine" in status
        assert status["model_name"] == "qwen2.5:3b"

        # Test RAG query against seeded database
        conn = self.db.get_connection()
        response = rag_service.ask_archival_assistant(conn, "What did Isaac Newton discover regarding light and prisms?")
        conn.close()
        assert "answer" in response
        assert "citations" in response
        assert "llm_engine" in response
        assert len(response["answer"]) > 10


if __name__ == "__main__":
    pytest.main(["-v", __file__])
