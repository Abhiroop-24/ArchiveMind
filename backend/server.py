"""
ArchiveMind Backend API Server
Course: UE23CS351A - DBMS Project | PES University
FastAPI Server providing RESTful endpoints for Hybrid Search,
Document Ingestion & Digital Preservation, Provenance Graph Traversal, and DBMS Query Execution.
"""

import os
import sys
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Ensure database package is accessible
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from database.db_manager import ArchiveMindDB, generate_deterministic_embedding

app = FastAPI(
    title="ArchiveMind API",
    description="Hybrid SQL-Vector Semantic Search Engine for Digitized Document Repositories",
    version="1.0.0"
)

db = ArchiveMindDB()

# Models
class HybridSearchRequest(BaseModel):
    query_text: Optional[str] = ""
    style_seed: Optional[str] = None
    alpha: float = 0.5
    collection_id: Optional[int] = None
    physical_condition: Optional[str] = None
    author_id: Optional[int] = None
    limit: int = 12

class IngestDocumentRequest(BaseModel):
    title: str
    collection_id: int
    doc_type: str
    date_written: str
    ocr_text: str
    author_name: str
    physical_condition: str = "Good"
    language: str = "English"
    style_seed: str = "standard_historical_cursive"
    digitized_by: int = 3
    image_name: str = "scanned_document.jpg"

class CitationRequest(BaseModel):
    style: str = "Chicago-Archival"
    user_id: Optional[int] = 3

class QueryRunRequest(BaseModel):
    query_key: str
    user_id: Optional[int] = 3

# -------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "healthy", "project": "ArchiveMind", "course": "UE23CS351A"}

@app.get("/api/meta")
def get_metadata():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT collection_id, name, era FROM collection")
    collections = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT person_id, full_name FROM person")
    persons = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT archive_id, name, institution FROM archive")
    archives = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {
        "collections": collections,
        "persons": persons,
        "archives": archives,
        "conditions": ["Pristine", "Good", "Fragile", "Critical-Decay"],
        "doc_types": ["Manuscript", "Letter", "Decree", "Mathematical Treatise", "Notebook", "Map"]
    }

@app.post("/api/search/hybrid")
def perform_hybrid_search(req: HybridSearchRequest):
    sample_vec = None
    if req.style_seed and req.style_seed.strip():
        sample_vec = generate_deterministic_embedding(req.style_seed.strip())

    results = db.hybrid_search(
        query_text=req.query_text or "",
        sample_vector=sample_vec,
        alpha=req.alpha,
        collection_id=req.collection_id,
        physical_condition=req.physical_condition,
        author_id=req.author_id,
        limit=req.limit
    )
    return {
        "query_text": req.query_text,
        "style_seed": req.style_seed,
        "alpha": req.alpha,
        "count": len(results),
        "results": results
    }

@app.get("/api/documents")
def list_documents():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            d.document_id, d.title, d.doc_type, d.date_written, d.physical_condition,
            d.language, d.ocr_status, d.checksum_value,
            c.name AS collection_name, c.era,
            a.name AS archive_name,
            GROUP_CONCAT(p.full_name, ', ') AS authors
        FROM document d
        JOIN collection c ON d.collection_id = c.collection_id
        JOIN archive a ON c.archive_id = a.archive_id
        LEFT JOIN document_author da ON d.document_id = da.document_id
        LEFT JOIN person p ON da.person_id = p.person_id
        GROUP BY d.document_id
        ORDER BY d.document_id ASC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/api/documents/{doc_id}")
def get_document_details(doc_id: int, request: Request, user_id: Optional[int] = 3):
    # Trigger view audit logging
    client_ip = request.client.host if request.client else "127.0.0.1"
    db.record_document_view(doc_id, user_id, client_ip)

    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            d.*,
            c.name AS collection_name, c.era,
            a.name AS archive_name, a.institution, a.location,
            u.full_name AS digitized_by_name,
            GROUP_CONCAT(p.full_name, ', ') AS authors
        FROM document d
        JOIN collection c ON d.collection_id = c.collection_id
        JOIN archive a ON c.archive_id = a.archive_id
        LEFT JOIN app_user u ON d.digitized_by = u.user_id
        LEFT JOIN document_author da ON d.document_id = da.document_id
        LEFT JOIN person p ON da.person_id = p.person_id
        WHERE d.document_id = ?
        GROUP BY d.document_id
    """, (doc_id,))
    doc = cur.fetchone()
    if not doc:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")

    cur.execute("SELECT * FROM citation WHERE document_id = ? ORDER BY generated_at DESC", (doc_id,))
    citations = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT sample_id, vector_id, extraction_method, extracted_at FROM handwriting_sample WHERE document_id = ?", (doc_id,))
    samples = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT dv.view_id, dv.viewed_at, dv.ip_address, COALESCE(u.full_name, 'Guest') AS viewer_name
        FROM document_view dv
        LEFT JOIN app_user u ON dv.user_id = u.user_id
        WHERE dv.document_id = ?
        ORDER BY dv.viewed_at DESC LIMIT 10
    """, (doc_id,))
    views = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {
        "document": dict(doc),
        "citations": citations,
        "handwriting_samples": samples,
        "audit_views": views
    }

@app.post("/api/documents/ingest")
def ingest_document(req: IngestDocumentRequest):
    try:
        res = db.ingest_document(
            title=req.title,
            collection_id=req.collection_id,
            doc_type=req.doc_type,
            date_written=req.date_written,
            ocr_text=req.ocr_text,
            author_name=req.author_name,
            physical_condition=req.physical_condition,
            language=req.language,
            style_seed=req.style_seed,
            digitized_by=req.digitized_by,
            image_name=req.image_name
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/documents/{doc_id}/citation")
def generate_doc_citation(doc_id: int, req: CitationRequest):
    try:
        res = db.generate_citation(doc_id, req.style, req.user_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/provenance/{doc_id}")
def get_provenance(doc_id: int):
    return db.get_provenance_graph(doc_id)

@app.get("/api/users")
def list_system_users():
    return db.get_all_users()

@app.get("/api/queries")
def list_queries():
    return [
        {"key": "7.1", "name": "7.1 Simple Query with GROUP BY & AGGREGATE", "category": "Aggregation"},
        {"key": "7.2", "name": "7.2 UPDATE Operation", "category": "Mutation"},
        {"key": "7.3", "name": "7.3 DELETE Operation", "category": "Mutation"},
        {"key": "7.4", "name": "7.4 Correlated Subquery", "category": "Subquery"},
        {"key": "7.5", "name": "7.5 Nested Subquery", "category": "Subquery"}
    ]

@app.post("/api/queries/run")
def run_query(req: QueryRunRequest):
    # Enforce Role-Based Access Control (RBAC) on database mutation operations
    user_role = db.get_user_role(req.user_id)
    if req.query_key in ["7.2", "7.3"] and user_role != "Head Archivist":
        raise HTTPException(
            status_code=403, 
            detail=f"RBAC Permission Denied: Query {req.query_key} modifies relational records and requires 'Head Archivist' (Demo Teacher) privileges. Current role: '{user_role}'."
        )
    try:
        res = db.run_evaluation_query(req.query_key)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/audit/views")
def list_audit_trail(limit: int = 25):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            dv.view_id, dv.viewed_at, dv.ip_address,
            d.document_id, d.title,
            COALESCE(u.full_name, 'Guest Researcher') AS viewer_name,
            r.role_name
        FROM document_view dv
        JOIN document d ON dv.document_id = d.document_id
        LEFT JOIN app_user u ON dv.user_id = u.user_id
        LEFT JOIN role r ON u.role_id = r.role_id
        ORDER BY dv.viewed_at DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# Serve frontend directory
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                return f.read()
        return "<h1>ArchiveMind Frontend Initializing...</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)

