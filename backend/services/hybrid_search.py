"""
ArchiveMind - Hybrid SQL + Vector Semantic Search Engine
Fuses SQLite FTS5 Full-Text Search and all-MiniLM-L6-v2 dense vector embeddings.
Supports Keyword-Only, Semantic-Only, Weighted Alpha Score Fusion, and Reciprocal Rank Fusion (RRF).
"""

import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional

try:
    from . import embedding_service
except ImportError:
    import embedding_service


def execute_hybrid_search(
    conn: sqlite3.Connection,
    query_text: str,
    alpha: float = 0.5,
    collection_id: Optional[int] = None,
    physical_condition: Optional[str] = None,
    author_id: Optional[int] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Executes hybrid retrieval:
    1. Runs SQLite FTS5 query to get keyword relevance scores.
    2. Runs MiniLM vector query against chunk embeddings to get semantic cosine scores.
    3. Normalizes both scores into [0.0, 1.0].
    4. Combines scores using HybridScore = alpha * K_score + (1 - alpha) * S_score.
    5. Retrieves best matching passage chunk for each document.
    """
    cur = conn.cursor()
    clean_q = query_text.strip() if query_text else ""

    # Step 1: Base metadata filtering
    where_clauses = ["1=1"]
    filter_params = []
    if collection_id:
        where_clauses.append("d.collection_id = ?")
        filter_params.append(collection_id)
    if physical_condition:
        where_clauses.append("d.physical_condition = ?")
        filter_params.append(physical_condition)
    if author_id:
        where_clauses.append("EXISTS (SELECT 1 FROM document_author da WHERE da.document_id = d.document_id AND da.person_id = ?)")
        filter_params.append(author_id)

    filter_sql = " AND ".join(where_clauses)

    # Fetch all eligible documents
    docs_query = f"""
        SELECT 
            d.document_id, d.title, d.doc_type, d.date_written, d.physical_condition,
            d.language, d.ocr_text_cache, d.checksum_value, d.image_path,
            c.name AS collection_name, c.era,
            a.name AS archive_name,
            GROUP_CONCAT(DISTINCT p.full_name) AS authors
        FROM document d
        JOIN collection c ON d.collection_id = c.collection_id
        JOIN archive a ON c.archive_id = a.archive_id
        LEFT JOIN document_author da ON d.document_id = da.document_id
        LEFT JOIN person p ON da.person_id = p.person_id
        WHERE {filter_sql}
        GROUP BY d.document_id
    """
    cur.execute(docs_query, filter_params)
    all_docs = {r["document_id"]: dict(r) for r in cur.fetchall()}

    if not all_docs:
        return []

    # Step 2: Keyword Search (SQLite FTS5)
    keyword_scores: Dict[int, float] = {}
    if clean_q:
        # Sanitize query for FTS5 (escape quotes and special tokens)
        sanitized_fts = clean_q.replace('"', '""').replace("'", "''")
        tokens = [f'"{tok}"' for tok in sanitized_fts.split() if tok.isalnum()]
        fts_match_expr = " OR ".join(tokens) if tokens else f'"{sanitized_fts}"'

        try:
            cur.execute(f"""
                SELECT 
                    document_id,
                    bm25(document_fts) AS raw_rank
                FROM document_fts
                WHERE document_fts MATCH ?
            """, (fts_match_expr,))
            fts_rows = cur.fetchall()
            for r in fts_rows:
                doc_id = int(r["document_id"])
                if doc_id in all_docs:
                    # FTS5 bm25 returns negative scores (lower is better, e.g. -5.2)
                    raw_val = float(r["raw_rank"])
                    # Convert to positive score: -raw_val
                    keyword_scores[doc_id] = max(0.01, -raw_val)
        except Exception:
            # Fallback to LIKE substring search if FTS syntax error
            for doc_id, doc in all_docs.items():
                content = (doc["title"] + " " + (doc["ocr_text_cache"] or "")).lower()
                matches = sum(1 for tok in clean_q.lower().split() if tok in content)
                if matches > 0:
                    keyword_scores[doc_id] = float(matches)

    # Normalize keyword scores to [0.0, 1.0]
    max_k = max(keyword_scores.values()) if keyword_scores else 1.0
    norm_keyword = {doc_id: round(score / max_k, 4) for doc_id, score in keyword_scores.items()}

    # Step 3: Real Semantic Vector Search (all-MiniLM-L6-v2)
    semantic_scores: Dict[int, float] = {}
    best_matching_passages: Dict[int, str] = {}

    if clean_q:
        try:
            query_vector = embedding_service.encode_query(clean_q)
            # Retrieve all chunk embeddings for candidate documents
            doc_id_placeholders = ",".join("?" for _ in all_docs.keys())
            cur.execute(f"""
                SELECT 
                    dc.document_id,
                    dc.chunk_text,
                    ce.embedding_blob
                FROM document_chunk dc
                JOIN chunk_embedding ce ON dc.chunk_id = ce.chunk_id
                WHERE dc.document_id IN ({doc_id_placeholders})
            """, list(all_docs.keys()))
            chunk_rows = cur.fetchall()

            for r in chunk_rows:
                doc_id = r["document_id"]
                blob = r["embedding_blob"]
                chunk_vec = embedding_service.blob_to_vector(blob)
                sim = embedding_service.compute_cosine_similarity(query_vector, chunk_vec)

                if doc_id not in semantic_scores or sim > semantic_scores[doc_id]:
                    semantic_scores[doc_id] = sim
                    best_matching_passages[doc_id] = r["chunk_text"]
        except Exception as e:
            # Fallback if embeddings not yet initialized
            pass

    # Step 4: Combine into Hybrid Score
    results = []
    # Rank lists for Reciprocal Rank Fusion (RRF)
    k_sorted_docs = sorted(all_docs.keys(), key=lambda d: norm_keyword.get(d, 0.0), reverse=True)
    s_sorted_docs = sorted(all_docs.keys(), key=lambda d: semantic_scores.get(d, 0.0), reverse=True)

    k_ranks = {doc_id: i + 1 for i, doc_id in enumerate(k_sorted_docs)}
    s_ranks = {doc_id: i + 1 for i, doc_id in enumerate(s_sorted_docs)}

    for doc_id, doc in all_docs.items():
        k_val = norm_keyword.get(doc_id, 0.0)
        s_val = round(semantic_scores.get(doc_id, 0.0), 4)

        # Weighted Score Fusion
        hybrid_score = round(alpha * k_val + (1.0 - alpha) * s_val, 4)

        # RRF (k=60)
        rrf_score = round((1.0 / (60 + k_ranks[doc_id])) + (1.0 / (60 + s_ranks[doc_id])), 6)

        # Extract matching passage or snippet
        matched_passage = best_matching_passages.get(doc_id)
        if not matched_passage:
            # Provide snippet from OCR text cache
            text = doc["ocr_text_cache"] or ""
            matched_passage = text[:180] + "..." if len(text) > 180 else text

        results.append({
            "document_id": doc_id,
            "title": doc["title"],
            "doc_type": doc["doc_type"],
            "date_written": doc["date_written"],
            "physical_condition": doc["physical_condition"],
            "language": doc["language"],
            "collection_name": doc["collection_name"],
            "era": doc["era"],
            "archive_name": doc["archive_name"],
            "authors": doc["authors"] or "Unknown",
            "image_path": doc["image_path"],
            "checksum_value": doc["checksum_value"],
            "keyword_score": k_val,
            "semantic_score": s_val,
            "hybrid_score": hybrid_score,
            "rrf_score": rrf_score,
            "matching_passage": matched_passage,
            "match_mode": "Hybrid (SQL+Vector)" if (k_val > 0 and s_val > 0) else ("SQL Keyword" if k_val > 0 else "Semantic Vector")
        })

    # Sort results by Hybrid Score descending
    results.sort(key=lambda x: (x["hybrid_score"], x["semantic_score"], x["keyword_score"]), reverse=True)
    return results[:limit]
