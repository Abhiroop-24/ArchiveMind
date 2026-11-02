"""
ArchiveMind Backend API Server
Course: VDUI Project
FastAPI Server providing RESTful endpoints for Hybrid Search (SQL+Vector),
Edge Raspberry Pi Acquisition, Background AI Ingestion, Provenance Graph Traversal,
Local RAG Research Assistant, and DBMS Evaluation Query Execution.
"""

import os
import sys
import uuid
import time
import shutil
import threading
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel

# Ensure base dir is accessible
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from database.db_manager import ArchiveMindDB, generate_deterministic_embedding
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

app = FastAPI(
    title="ArchiveMind — Hybrid SQL-Vector Archival Platform",
    description="Intelligent Archival Acquisition, Vision Processing, Real MiniLM Semantic Retrieval & Local RAG",
    version="2.0.0"
)

db = ArchiveMindDB()

STORAGE_DIR = os.path.join(BASE_DIR, "storage")
ORIGINALS_DIR = os.path.join(STORAGE_DIR, "originals")
PROCESSED_DIR = os.path.join(STORAGE_DIR, "processed")
UPLOADS_DIR = os.path.join(STORAGE_DIR, "uploads")

for d in (ORIGINALS_DIR, PROCESSED_DIR, UPLOADS_DIR):
    os.makedirs(d, exist_ok=True)


# -------------------------------------------------------------
# Pydantic Schemas
# -------------------------------------------------------------

class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_name: str
    device_type: str = "Raspberry Pi 3B+ (5MP ov5647)"
    ip_address: str = "10.42.0.116"

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

class OCRUpdateRequest(BaseModel):
    corrected_text: str

class AssistantAskRequest(BaseModel):
    question: str

class CitationRequest(BaseModel):
    style: str = "Chicago-Archival"
    user_id: Optional[int] = 3

class QueryRunRequest(BaseModel):
    query_key: str
    user_id: Optional[int] = 3

class RemoteCaptureRequest(BaseModel):
    device_id: str = "archivemind-pi-cam-01"
    pi_ip: str = "10.42.0.116"
    pi_port: int = 8082
    backup_pi_ip: Optional[str] = "192.168.1.9"


# -------------------------------------------------------------
# CORE & HEALTH APIS
# -------------------------------------------------------------

@app.get("/api/health")
def health():
    gpu_available = False
    gpu_name = "CPU Mode"
    try:
        import torch
        if torch.cuda.is_available():
            gpu_available = True
            gpu_name = torch.cuda.get_device_name(0)
    except Exception:
        pass

    return {
        "status": "healthy",
        "project": "ArchiveMind — AI-Powered Hybrid SQL–Vector Semantic Search Engine",
        "course": "VDUI",
        "version": "2.0.0",
        "gpu_available": gpu_available,
        "compute_device": gpu_name,
        "models_active": [
            "sentence-transformers/all-MiniLM-L6-v2",
            "MobileNetV3-Small-ArchivalCondition",
            "TrOCR-Base-Handwritten",
            "SQLite FTS5 BM25 Engine"
        ]
    }

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
    cur.execute("SELECT COUNT(*) AS total_docs FROM document")
    total_docs = cur.fetchone()["total_docs"]
    conn.close()

    return {
        "collections": collections,
        "persons": persons,
        "archives": archives,
        "total_documents": total_docs,
        "conditions": ["Pristine", "Good", "Fragile", "Critical-Decay"],
        "doc_types": ["Manuscript", "Letter", "Decree", "Mathematical Treatise", "Notebook", "Map"]
    }


# -------------------------------------------------------------
# RASPBERRY PI & HARDWARE DEVICE APIS
# -------------------------------------------------------------

@app.post("/api/devices/register")
def register_device_api(req: DeviceRegisterRequest):
    db.register_device(
        device_id=req.device_id,
        device_name=req.device_name,
        device_type=req.device_type,
        ip_address=req.ip_address
    )
    return {"success": True, "message": f"Device '{req.device_id}' registered successfully."}

@app.get("/api/devices")
def list_devices():
    return db.get_devices()

@app.get("/api/devices/{device_id}/status")
def get_device_status_api(device_id: str):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM device WHERE device_id = ?", (device_id,))
    dev = cur.fetchone()
    conn.close()
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")

    import subprocess
    eth_ip = "10.42.0.116"
    wifi_ip = "192.168.1.9"

    eth_live = False
    wifi_live = False
    try:
        eth_live = (subprocess.run(["ping", "-c", "1", "-W", "1", eth_ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)
    except Exception:
        pass
    try:
        wifi_live = (subprocess.run(["ping", "-c", "1", "-W", "1", wifi_ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)
    except Exception:
        pass

    active_ip = eth_ip if eth_live else (wifi_ip if wifi_live else eth_ip)
    active_route = "Direct Ethernet (10.42.0.116)" if eth_live else ("Campus/Home Wi-Fi (192.168.1.9)" if wifi_live else "Offline")

    return {
        "device": dict(dev),
        "is_reachable": eth_live or wifi_live,
        "ethernet_ip": eth_ip,
        "ethernet_live": eth_live,
        "wifi_ip": wifi_ip,
        "wifi_live": wifi_live,
        "active_ip": active_ip,
        "active_route": active_route,
        "network_interface": f"Dual-Homed: Ethernet ({eth_ip}) | Wi-Fi ({wifi_ip})",
        "camera_module": "Raspberry Pi Camera Module 5MP (ov5647)"
    }

@app.post("/api/devices/trigger_capture")
def trigger_remote_capture(req: RemoteCaptureRequest):
    """
    Sends an HTTP capture command to the Raspberry Pi daemon.
    Tries primary Ethernet (10.42.0.116:8082) first, and falls back to Wi-Fi (192.168.1.9:8082).
    """
    import urllib.request
    import json

    candidate_hosts = [req.pi_ip]
    if req.backup_pi_ip and req.backup_pi_ip not in candidate_hosts:
        candidate_hosts.append(req.backup_pi_ip)

    last_error = None
    for host in candidate_hosts:
        url = f"http://{host}:{req.pi_port}/capture"
        try:
            remote_req = urllib.request.Request(
                url,
                data=b"{}",
                headers={"Content-Type": "application/json", "User-Agent": "ArchiveMind-Server/2.0"},
                method="POST"
            )
            with urllib.request.urlopen(remote_req, timeout=12.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "success": True,
                    "active_endpoint": url,
                    "target_host": host,
                    "message": f"Capture command dispatched successfully to Pi via {host}",
                    "pi_response": data
                }
        except Exception as e:
            last_error = e
            continue

    raise HTTPException(
        status_code=502,
        detail=f"Failed to communicate with Raspberry Pi on endpoints {candidate_hosts}: {str(last_error)}"
    )


# -------------------------------------------------------------
# INGESTION APIS (IMAGE UPLOAD & ASYNC PIPELINE)
# -------------------------------------------------------------

@app.post("/api/ingestion/upload")
async def upload_manuscript_image(
    file: UploadFile = File(...),
    scan_id: Optional[str] = Form(None),
    device_id: Optional[str] = Form(None),
    checksum_sha256: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    collection_id: int = Form(1),
    author_name: str = Form("Unknown Manuscript Author"),
    doc_type: str = Form("Manuscript"),
    date_written: str = Form("Circa 17th Century"),
    language: str = Form("English"),
    ocr_mode: str = Form("auto"),
    background_tasks: BackgroundTasks = None
):
    """
    Accepts raw image upload from Raspberry Pi or Web Client.
    Saves image into storage/originals, creates an ingestion job, and starts background processing.
    """
    actual_scan_id = scan_id or f"scan_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    job_id = f"job_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    
    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    orig_filename = f"{actual_scan_id}{file_ext}"
    orig_path = os.path.join(ORIGINALS_DIR, orig_filename)

    with open(orig_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Register device if specified
    if device_id:
        db.register_device(device_id, "Raspberry Pi Client", "Raspberry Pi 3B+", "10.42.0.116")

    # Create Ingestion Job Record
    db.create_ingestion_job(
        job_id=job_id,
        scan_id=actual_scan_id,
        original_image_path=orig_path,
        device_id=device_id
    )

    # Launch background processing pipeline
    def run_worker():
        process_ingestion_pipeline(
            db_path=db.db_path,
            job_id=job_id,
            original_image_path=orig_path,
            scan_id=actual_scan_id,
            device_id=device_id,
            document_title=title,
            collection_id=collection_id,
            doc_type=doc_type,
            date_written=date_written,
            author_name=author_name,
            language=language,
            ocr_mode=ocr_mode
        )

    t = threading.Thread(target=run_worker, daemon=True)
    t.start()

    return {
        "success": True,
        "job_id": job_id,
        "scan_id": actual_scan_id,
        "status": "PROCESSING",
        "message": "Image received and queued for CV enhancement, OCR, and MiniLM semantic indexing.",
        "image_path": f"/storage/originals/{orig_filename}"
    }

@app.get("/api/ingestion/jobs")
def list_ingestion_jobs(limit: int = 20):
    return db.get_ingestion_jobs(limit=limit)

@app.get("/api/ingestion/jobs/{job_id}")
def get_ingestion_job_status(job_id: str):
    job = db.get_ingestion_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    return job


# -------------------------------------------------------------
# HYBRID & SEMANTIC SEARCH APIS
# -------------------------------------------------------------

@app.post("/api/search/hybrid")
def perform_hybrid_search(req: HybridSearchRequest):
    """
    Combines SQLite FTS5 BM25 keyword search and real all-MiniLM-L6-v2 vector embeddings.
    """
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
        "alpha": req.alpha,
        "model_used": "sentence-transformers/all-MiniLM-L6-v2 (384-d)",
        "fusion_method": f"Linear Score Fusion (alpha={req.alpha}) + Reciprocal Rank Fusion",
        "count": len(results),
        "results": results
    }

@app.post("/api/search/semantic")
def perform_semantic_only_search(req: HybridSearchRequest):
    """Pure semantic search with alpha=0.0."""
    req.alpha = 0.0
    return perform_hybrid_search(req)


# -------------------------------------------------------------
# LOCAL RAG RESEARCH ASSISTANT API
# -------------------------------------------------------------

@app.post("/api/assistant/ask")
def ask_assistant_api(req: AssistantAskRequest):
    """
    Local RAG endpoint:
    Retrieves grounded passages and generates citation-backed answers via Ollama or extractive synthesizer.
    """
    conn = db.get_connection()
    try:
        response = rag_service.ask_archival_assistant(conn, req.question)
        return response
    finally:
        conn.close()


# -------------------------------------------------------------
# AI MODELS & HARDWARE METRICS
# -------------------------------------------------------------

@app.get("/api/models/status")
def get_models_status():
    import psutil
    mem = psutil.virtual_memory()

    gpu_info = {"available": False, "device": "CPU Fallback"}
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info = {
                "available": True,
                "device": torch.cuda.get_device_name(0),
                "vram_total_mb": round(torch.cuda.get_device_properties(0).total_memory / 1024 / 1024, 1),
                "vram_allocated_mb": round(torch.cuda.memory_allocated(0) / 1024 / 1024, 1)
            }
    except Exception:
        pass

    return {
        "models": db.get_model_registry(),
        "hardware": {
            "ram_total_gb": round(mem.total / (1024**3), 1),
            "ram_used_gb": round(mem.used / (1024**3), 1),
            "ram_percent": mem.percent,
            "gpu": gpu_info
        },
        "embedding_service": embedding_service.get_model_info()
    }


# -------------------------------------------------------------
# DOCUMENT & CITATION APIS (PRESERVED)
# -------------------------------------------------------------

@app.get("/api/documents")
def list_documents():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            d.document_id, d.title, d.doc_type, d.date_written, d.physical_condition,
            d.language, d.ocr_status, d.checksum_value, d.image_path,
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

    cur.execute("SELECT * FROM ml_prediction WHERE document_id = ? ORDER BY created_at DESC", (doc_id,))
    predictions = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM document_image WHERE document_id = ?", (doc_id,))
    images = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT chunk_id, chunk_index, chunk_text FROM document_chunk WHERE document_id = ? ORDER BY chunk_index ASC", (doc_id,))
    chunks = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {
        "document": dict(doc),
        "citations": citations,
        "handwriting_samples": samples,
        "audit_views": views,
        "predictions": predictions,
        "images": images,
        "chunks": chunks
    }

@app.patch("/api/documents/{doc_id}/ocr")
def update_document_ocr_api(doc_id: int, req: OCRUpdateRequest):
    db.update_document_ocr(doc_id, req.corrected_text)
    return {"success": True, "message": "OCR text updated, FTS5 indexed, and semantic vectors regenerated."}

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


# -------------------------------------------------------------
# STATIC FILES & WEB DASHBOARD
# -------------------------------------------------------------

# Mount storage directory to serve original and processed images
app.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage")

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

    @app.get("/report", response_class=HTMLResponse)
    def view_report():
        report_file = os.path.join(BASE_DIR, "docs", "ArchiveMind_DBMS_Project_Report.html")
        if os.path.exists(report_file):
            with open(report_file, "r", encoding="utf-8") as f:
                return f.read()
        return "<h1>Report file not found</h1>"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
