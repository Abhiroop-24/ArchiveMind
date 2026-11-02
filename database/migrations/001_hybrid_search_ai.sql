-- ==============================================================================
-- ArchiveMind Migration 001: AI/ML Hybrid Search & Raspberry Pi Ingestion Tables
-- ==============================================================================

-- 1. Device Registration (Raspberry Pi acquisition units)
CREATE TABLE IF NOT EXISTS device (
    device_id TEXT PRIMARY KEY,
    device_name TEXT NOT NULL,
    device_type TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'ONLINE' CHECK (status IN ('ONLINE', 'OFFLINE', 'ACQUIRING'))
);

-- 2. Ingestion Jobs
CREATE TABLE IF NOT EXISTS ingestion_job (
    job_id TEXT PRIMARY KEY,
    device_id TEXT REFERENCES device(device_id) ON DELETE SET NULL,
    scan_id TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    original_image_path TEXT NOT NULL,
    enhanced_image_path TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 3. Document Images (Filesystem pointers & cryptographic verification)
CREATE TABLE IF NOT EXISTS document_image (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER REFERENCES document(document_id) ON DELETE CASCADE,
    job_id TEXT REFERENCES ingestion_job(job_id) ON DELETE SET NULL,
    original_path TEXT NOT NULL,
    processed_path TEXT,
    sha256 TEXT NOT NULL,
    width INTEGER DEFAULT 1920,
    height INTEGER DEFAULT 1080,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. OCR & Handwriting Recognition Results
CREATE TABLE IF NOT EXISTS ocr_result (
    ocr_id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER REFERENCES document_image(image_id) ON DELETE CASCADE,
    engine TEXT NOT NULL,
    model_name TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    corrected_text TEXT,
    confidence REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Document Text Chunks
CREATE TABLE IF NOT EXISTS document_chunk (
    chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    source_ocr_id INTEGER REFERENCES ocr_result(ocr_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Real Semantic Embeddings (Float32 Binary BLOB for all-MiniLM-L6-v2)
CREATE TABLE IF NOT EXISTS chunk_embedding (
    chunk_id INTEGER PRIMARY KEY REFERENCES document_chunk(chunk_id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    dimensions INTEGER NOT NULL DEFAULT 384,
    embedding_blob BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Machine Learning Predictions (Damage assessment, script classification)
CREATE TABLE IF NOT EXISTS ml_prediction (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER REFERENCES document(document_id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    prediction_type TEXT NOT NULL,
    predicted_label TEXT NOT NULL,
    confidence REAL NOT NULL,
    reviewed_label TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Model Registry & Metadata
CREATE TABLE IF NOT EXISTS model_registry (
    model_id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    model_type TEXT NOT NULL,
    model_path TEXT,
    evaluation_metrics TEXT,
    active INTEGER DEFAULT 1
);

-- Indexes for Fast Retrieval
CREATE INDEX IF NOT EXISTS idx_doc_chunk_doc_id ON document_chunk(document_id);
CREATE INDEX IF NOT EXISTS idx_doc_image_doc_id ON document_image(document_id);
CREATE INDEX IF NOT EXISTS idx_ml_pred_doc_id ON ml_prediction(document_id);
CREATE INDEX IF NOT EXISTS idx_ingest_job_status ON ingestion_job(status);
CREATE INDEX IF NOT EXISTS idx_device_status ON device(status);
