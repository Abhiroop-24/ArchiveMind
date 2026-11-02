-- ====================================================================
-- ARCHIVEMIND: A Hybrid SQL-Vector Semantic Search Engine for Digitized Document Repositories
-- Course: UE23CS351A - DBMS Project | PES University
-- Target DBMS: PostgreSQL 15+ (with pgvector & tsvector support)
-- ====================================================================

-- Enable vector extension for handwriting & semantic embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. ROLE TABLE
CREATE TABLE role (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL CHECK (role_name IN ('Head Archivist', 'Researcher', 'Digitization Tech', 'Auditor'))
);

-- 2. APP_USER TABLE
CREATE TABLE app_user (
    user_id SERIAL PRIMARY KEY,
    role_id INT NOT NULL REFERENCES role(role_id) ON DELETE RESTRICT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. ARCHIVE TABLE
CREATE TABLE archive (
    archive_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    location VARCHAR(150) NOT NULL,
    institution VARCHAR(150) NOT NULL
);

-- 4. COLLECTION TABLE
CREATE TABLE collection (
    collection_id SERIAL PRIMARY KEY,
    archive_id INT NOT NULL REFERENCES archive(archive_id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    era VARCHAR(80) NOT NULL,
    description TEXT
);

-- 5. ACCESS_PERMISSION TABLE (Role-Based & Collection-Level Granular Security)
CREATE TABLE access_permission (
    permission_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
    collection_id INT NOT NULL REFERENCES collection(collection_id) ON DELETE CASCADE,
    permission_type VARCHAR(20) NOT NULL CHECK (permission_type IN ('READ', 'WRITE', 'ADMIN')),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_collection UNIQUE (user_id, collection_id)
);

-- 6. DOCUMENT TABLE
CREATE TABLE document (
    document_id SERIAL PRIMARY KEY,
    collection_id INT NOT NULL REFERENCES collection(collection_id) ON DELETE CASCADE,
    digitized_by INT REFERENCES app_user(user_id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    doc_type VARCHAR(50) NOT NULL CHECK (doc_type IN ('Manuscript', 'Letter', 'Decree', 'Mathematical Treatise', 'Notebook', 'Map')),
    date_written VARCHAR(50),
    ocr_text_cache TEXT,
    search_vector tsvector, -- Full-Text Search tsvector
    checksum_value VARCHAR(64) NOT NULL, -- SHA-256 for cryptographic integrity
    checksum_algorithm VARCHAR(20) DEFAULT 'SHA-256',
    physical_condition VARCHAR(30) CHECK (physical_condition IN ('Pristine', 'Good', 'Fragile', 'Critical-Decay')),
    language VARCHAR(50) DEFAULT 'English',
    image_path VARCHAR(500) NOT NULL,
    ocr_status VARCHAR(20) DEFAULT 'COMPLETED' CHECK (ocr_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    digitized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. PERSON TABLE (Historical Figures, Authors, Scribes)
CREATE TABLE person (
    person_id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    birth_year INT,
    death_year INT,
    biography TEXT,
    CONSTRAINT chk_years CHECK (death_year IS NULL OR birth_year IS NULL OR death_year >= birth_year)
);

-- 8. DOCUMENT_AUTHOR TABLE (M:N Associative Entity)
CREATE TABLE document_author (
    document_id INT NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
    person_id INT NOT NULL REFERENCES person(person_id) ON DELETE RESTRICT,
    attribution_type VARCHAR(50) DEFAULT 'Author' CHECK (attribution_type IN ('Author', 'Scribe', 'Signatory', 'Recipient', 'Annotator')),
    confidence_score NUMERIC(3, 2) DEFAULT 1.00 CHECK (confidence_score >= 0.00 AND confidence_score <= 1.00),
    PRIMARY KEY (document_id, person_id)
);

-- 9. HANDWRITING_SAMPLE TABLE (Vector Embeddings for Forensic Stroke Analysis)
CREATE TABLE handwriting_sample (
    sample_id SERIAL PRIMARY KEY,
    document_id INT NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
    vector_id VARCHAR(64) NOT NULL,
    embedding vector(128), -- 128-dimensional dense visual feature vector
    extraction_method VARCHAR(50) DEFAULT 'ResNet50-Forensic-Extractor',
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. DOCUMENT_VIEW TABLE (Chain of Custody & Audit Trail)
CREATE TABLE document_view (
    view_id SERIAL PRIMARY KEY,
    document_id INT NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
    user_id INT REFERENCES app_user(user_id) ON DELETE SET NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45) NOT NULL
);

-- 11. CITATION TABLE
CREATE TABLE citation (
    citation_id SERIAL PRIMARY KEY,
    document_id INT NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
    citation_text TEXT NOT NULL,
    citation_style VARCHAR(30) DEFAULT 'Chicago-Archival',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- INDEXES FOR HYBRID RETRIEVAL OPTIMIZATION
-- ====================================================================

-- GIN Index for PostgreSQL Full-Text Search
CREATE INDEX idx_document_search_vector ON document USING gin(search_vector);

-- IVFFlat Index for High-Dimensional Vector Similarity Search (L2 or Cosine distance)
CREATE INDEX idx_handwriting_embedding ON handwriting_sample USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);

-- B-Tree Indexes on Foreign Keys and Query Filter attributes
CREATE INDEX idx_doc_collection ON document(collection_id);
CREATE INDEX idx_doc_condition ON document(physical_condition);
CREATE INDEX idx_view_doc_user ON document_view(document_id, user_id);

