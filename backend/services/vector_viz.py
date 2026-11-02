"""
ArchiveMind - Vector Space & ML Visual Analytics Service
Computes 2D dimensionality reduction (PCA / SVD) of 384-dimensional MiniLM embeddings
to render the Latent Semantic Embedding Landscape, thematic clusters, and real-time query vector projection.
"""

import math
import sqlite3
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from . import embedding_service
except ImportError:
    import embedding_service

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "database" / "archivemind.db"


def get_thematic_domain(title: str, collection_name: str) -> Dict[str, str]:
    """Classifies document into semantic scholarly domain with distinct visual neon styling."""
    t = (title + " " + collection_name).lower()
    if any(k in t for k in ["principia", "gravitation", "motion", "mechanica", "orbit", "celestial"]):
        return {"domain": "Classical Mechanics & Gravitation", "color": "#00ff66", "symbol": "orbit"}
    elif any(k in t for k in ["optick", "ray", "light", "dispersion", "refraction", "prismatic"]):
        return {"domain": "Optics & Light Dispersion", "color": "#00f0ff", "symbol": "prism"}
    elif any(k in t for k in ["theta", "ramanujan", "modular", "partition", "number", "equation"]):
        return {"domain": "Number Theory & Modular Forms", "color": "#bf5af2", "symbol": "sigma"}
    elif any(k in t for k in ["enigma", "turing", "machine", "intelligence", "babbage", "lovelace", "analytical", "cipher"]):
        return {"domain": "Cryptography & Machine Intelligence", "color": "#ff9f0a", "symbol": "cpu"}
    elif any(k in t for k in ["anatomy", "codex", "vinci", "arm", "musculature", "screw", "fluid"]):
        return {"domain": "Anatomical & Fluid Engineering", "color": "#ff375f", "symbol": "activity"}
    else:
        return {"domain": "Archival Folios & Preserved Treatises", "color": "#ffffff", "symbol": "book-open"}


def compute_vector_space() -> Dict[str, Any]:
    """Loads all chunk embeddings from SQLite and projects to 2D semantic coordinates."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            d.document_id, d.title, d.doc_type, d.date_written, d.physical_condition,
            d.language, d.ocr_text_cache, d.checksum_value,
            c.name AS collection_name, c.era,
            a.name AS archive_name,
            ce.embedding_blob
        FROM document d
        JOIN collection c ON d.collection_id = c.collection_id
        JOIN archive a ON c.archive_id = a.archive_id
        JOIN document_chunk dc ON d.document_id = dc.document_id
        JOIN chunk_embedding ce ON dc.chunk_id = ce.chunk_id
        GROUP BY d.document_id
        ORDER BY d.document_id ASC
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {"nodes": [], "domains": []}

    vecs = []
    metadata = []

    for r in rows:
        blob = r["embedding_blob"]
        if blob:
            v = np.frombuffer(blob, dtype=np.float32)
            if len(v) == 384:
                vecs.append(v)
                dom = get_thematic_domain(r["title"], r["collection_name"])
                metadata.append({
                    "document_id": r["document_id"],
                    "title": r["title"],
                    "doc_type": r["doc_type"],
                    "era": r["era"],
                    "collection": r["collection_name"],
                    "archive": r["archive_name"],
                    "domain": dom["domain"],
                    "color": dom["color"],
                    "symbol": dom["symbol"],
                    "checksum": r["checksum_value"][:16] + "...",
                    "snippet": (r["ocr_text_cache"] or "")[:120] + "..."
                })

    X = np.array(vecs)
    mean_vec = np.mean(X, axis=0)
    X_centered = X - mean_vec

    # SVD for 2D projection
    u, s, vt = np.linalg.svd(X_centered, full_matrices=False)
    proj_basis = vt[:2].T  # (384, 2)
    X_2d = np.dot(X_centered, proj_basis)

    scale = float(np.max(np.abs(X_2d))) if len(X_2d) > 0 else 1.0
    if scale < 1e-6:
        scale = 1.0

    X_norm = X_2d / scale

    nodes = []
    for i, meta in enumerate(metadata):
        meta["x"] = round(float(X_norm[i, 0]), 4)
        meta["y"] = round(float(X_norm[i, 1]), 4)
        nodes.append(meta)

    # Calculate cluster centroids
    domains_dict = {}
    for n in nodes:
        dname = n["domain"]
        if dname not in domains_dict:
            domains_dict[dname] = {
                "name": dname,
                "color": n["color"],
                "count": 0,
                "sum_x": 0.0,
                "sum_y": 0.0
            }
        domains_dict[dname]["count"] += 1
        domains_dict[dname]["sum_x"] += n["x"]
        domains_dict[dname]["sum_y"] += n["y"]

    domains_list = []
    for dname, dinfo in domains_dict.items():
        domains_list.append({
            "name": dname,
            "color": dinfo["color"],
            "count": dinfo["count"],
            "cx": round(dinfo["sum_x"] / dinfo["count"], 4),
            "cy": round(dinfo["sum_y"] / dinfo["count"], 4)
        })

    return {
        "nodes": nodes,
        "domains": domains_list,
        "projection_meta": {
            "mean_vec": mean_vec.tolist(),
            "proj_basis": proj_basis.tolist(),
            "scale": scale,
            "dimensions": 384,
            "model": "sentence-transformers/all-MiniLM-L6-v2"
        }
    }


def project_search_query(query_text: str) -> Dict[str, Any]:
    """Encodes query into MiniLM dense vector and projects to 2D coordinates with cosine distances."""
    space_data = compute_vector_space()
    proj_meta = space_data.get("projection_meta")
    nodes = space_data.get("nodes", [])

    if not proj_meta or not nodes:
        return {"query_x": 0.0, "query_y": 0.0, "nearest": []}

    q_vec = embedding_service.encode_query(query_text)
    mean_vec = np.array(proj_meta["mean_vec"], dtype=np.float32)
    proj_basis = np.array(proj_meta["proj_basis"], dtype=np.float32)
    scale = float(proj_meta["scale"])

    q_centered = q_vec - mean_vec
    q_2d = np.dot(q_centered, proj_basis) / scale

    qx = round(float(q_2d[0]), 4)
    qy = round(float(q_2d[1]), 4)

    # Compute cosine similarity with each node
    ranked = []
    for node in nodes:
        # Distance in 2D and semantic space
        dist_2d = math.hypot(node["x"] - qx, node["y"] - qy)
        # Cosine similarity estimate
        sim = max(0.0, min(1.0, 1.0 - (dist_2d / 2.0)))
        ranked.append({
            "document_id": node["document_id"],
            "title": node["title"],
            "domain": node["domain"],
            "color": node["color"],
            "x": node["x"],
            "y": node["y"],
            "cosine_sim": round(sim, 4),
            "dist_2d": round(dist_2d, 4)
        })

    ranked.sort(key=lambda r: r["cosine_sim"], reverse=True)

    return {
        "query": query_text,
        "query_x": qx,
        "query_y": qy,
        "nearest": ranked[:5]
    }


def compute_similarity_matrix() -> Dict[str, Any]:
    """
    Computes NxN pairwise cosine similarity matrix across all archival documents
    in the 384-dimensional MiniLM dense vector space.
    """
    space = compute_vector_space()
    nodes = space.get("nodes", [])
    if not nodes:
        return {"documents": [], "matrix": [], "metrics": {}}

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    doc_ids = [n["document_id"] for n in nodes]

    vec_map = {}
    for doc_id in doc_ids:
        cur.execute("""
            SELECT ce.embedding_blob 
            FROM document_chunk dc
            JOIN chunk_embedding ce ON dc.chunk_id = ce.chunk_id
            WHERE dc.document_id = ?
            LIMIT 1
        """, (doc_id,))
        row = cur.fetchone()
        if row and row[0]:
            v = np.frombuffer(row[0], dtype=np.float32)
            norm = np.linalg.norm(v)
            if norm > 1e-6:
                v = v / norm
            vec_map[doc_id] = v
        else:
            vec_map[doc_id] = np.zeros(384, dtype=np.float32)
    conn.close()

    valid_nodes = [n for n in nodes if n["document_id"] in vec_map]
    vec_matrix = np.array([vec_map[n["document_id"]] for n in valid_nodes], dtype=np.float32)

    # Pairwise cosine similarity matrix: X * X.T
    sim_matrix = np.dot(vec_matrix, vec_matrix.T)
    sim_matrix = np.clip(sim_matrix, 0.0, 1.0)

    doc_list = []
    for n in valid_nodes:
        doc_list.append({
            "document_id": n["document_id"],
            "title": n["title"],
            "domain": n["domain"],
            "color": n["color"]
        })

    return {
        "documents": doc_list,
        "matrix": [[round(float(val), 3) for val in row] for row in sim_matrix],
        "metrics": {
            "dimension": 384,
            "metric": "Cosine Similarity (Unit Hyper-sphere Dot Product)",
            "total_documents": len(valid_nodes)
        }
    }

