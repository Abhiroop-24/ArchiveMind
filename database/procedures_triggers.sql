-- ====================================================================
-- ARCHIVEMIND: Stored Procedures, Functions, and Triggers
-- Course: UE23CS351A - DBMS Project | PES University
-- ====================================================================

-- --------------------------------------------------------------------
-- 1. TRIGGER: Automatic Full-Text Search Vector Generator
-- --------------------------------------------------------------------
-- Updates the tsvector cache whenever a document title or OCR text is inserted or updated.
CREATE OR REPLACE FUNCTION fn_update_document_tsvector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.ocr_text_cache, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_document_tsv_update
BEFORE INSERT OR UPDATE OF title, ocr_text_cache ON document
FOR EACH ROW
EXECUTE FUNCTION fn_update_document_tsvector();

-- --------------------------------------------------------------------
-- 2. TRIGGER: Audit Trail Chain-of-Custody Integrity
-- --------------------------------------------------------------------
-- Ensures whenever a critical document is updated, the checksum is verified.
CREATE OR REPLACE FUNCTION fn_verify_document_integrity()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.checksum_value IS NULL OR length(NEW.checksum_value) < 32 THEN
        RAISE EXCEPTION 'Cryptographic checksum invalid. Document integrity cannot be validated.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_verify_integrity
BEFORE UPDATE ON document
FOR EACH ROW
EXECUTE FUNCTION fn_verify_document_integrity();

-- --------------------------------------------------------------------
-- 2b. TRIGGER: Automated Citation Generation Audit Logging
-- --------------------------------------------------------------------
-- Automatically logs an immutable audit event in DOCUMENT_VIEW when a citation is created
CREATE OR REPLACE FUNCTION fn_audit_citation_generation()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO document_view (document_id, user_id, ip_address, viewed_at)
    VALUES (
        NEW.document_id,
        COALESCE(NEW.user_id, 3), -- Dynamic operator (Abhiroop / Sheiman / Demo Teacher)
        '127.0.0.1 [TRIGGER:CITATION_' || UPPER(NEW.citation_style) || ']',
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_citation_generation
AFTER INSERT ON citation
FOR EACH ROW
EXECUTE FUNCTION fn_audit_citation_generation();

-- --------------------------------------------------------------------
-- 3. STORED PROCEDURE: Generate Archival Citation
-- --------------------------------------------------------------------
-- Formats standard archival citations (Chicago/MLA style) and inserts into CITATION table
CREATE OR REPLACE PROCEDURE sp_generate_archival_citation(
    IN p_document_id INT,
    IN p_style VARCHAR(30) DEFAULT 'Chicago-Archival'
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_title VARCHAR(255);
    v_date VARCHAR(50);
    v_archive_name VARCHAR(150);
    v_col_name VARCHAR(150);
    v_author_name VARCHAR(150);
    v_citation_text TEXT;
BEGIN
    -- Query metadata joining document, collection, archive, author
    SELECT 
        d.title, d.date_written, c.name, a.name, COALESCE(p.full_name, 'Unknown Author')
    INTO 
        v_title, v_date, v_col_name, v_archive_name, v_author_name
    FROM document d
    JOIN collection c ON d.collection_id = c.collection_id
    JOIN archive a ON c.archive_id = a.archive_id
    LEFT JOIN document_author da ON d.document_id = da.document_id
    LEFT JOIN person p ON da.person_id = p.person_id
    WHERE d.document_id = p_document_id
    LIMIT 1;

    IF v_title IS NULL THEN
        RAISE EXCEPTION 'Document ID % does not exist', p_document_id;
    END IF;

    -- Format citation string based on requested style
    IF p_style = 'MLA' THEN
        v_citation_text := v_author_name || '. "' || v_title || '." ' || v_date || '. ' || v_col_name || ', ' || v_archive_name || '. ArchiveMind Digitized Repository.';
    ELSE
        -- Chicago Archival style (Default)
        v_citation_text := v_author_name || ', ' || v_title || ' (' || v_date || '), ' || v_col_name || ', ' || v_archive_name || '. Digitized preservation record.';
    END IF;

    -- Insert or update citation record
    INSERT INTO citation (document_id, citation_text, citation_style, generated_at)
    VALUES (p_document_id, v_citation_text, p_style, CURRENT_TIMESTAMP);
    
    COMMIT;
END;
$$;

-- --------------------------------------------------------------------
-- 4. STORED PROCEDURE: Atomic Document Transfer Between Collections
-- --------------------------------------------------------------------
-- Safely reassigns a document from one collection to another within a transaction
CREATE OR REPLACE PROCEDURE sp_transfer_document_collection(
    IN p_document_id INT,
    IN p_new_collection_id INT,
    IN p_operator_user_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_old_collection_id INT;
BEGIN
    -- Check if document exists and get current collection
    SELECT collection_id INTO v_old_collection_id
    FROM document WHERE document_id = p_document_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Document with ID % not found.', p_document_id;
    END IF;

    -- Update document collection atomically
    UPDATE document
    SET collection_id = p_new_collection_id
    WHERE document_id = p_document_id;

    -- Log transaction in view/audit
    INSERT INTO document_view (document_id, user_id, ip_address)
    VALUES (p_document_id, p_operator_user_id, '127.0.0.1 [TRANSFER_EVENT]');

    COMMIT;
END;
$$;

-- --------------------------------------------------------------------
-- 5. FUNCTION: Hybrid Semantic & Vector Score Fusion
-- --------------------------------------------------------------------
-- Demonstrates hybrid query scoring combining Full-Text Search rank with Vector cosine similarity
CREATE OR REPLACE FUNCTION fn_hybrid_search(
    p_query_text TEXT,
    p_query_vector vector(128),
    p_alpha FLOAT DEFAULT 0.6,
    p_limit INT DEFAULT 10
)
RETURNS TABLE (
    document_id INT,
    title VARCHAR,
    fts_rank FLOAT,
    vector_similarity FLOAT,
    hybrid_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH fts_scores AS (
        SELECT 
            d.document_id,
            ts_rank(d.search_vector, plainto_tsquery('english', p_query_text))::FLOAT AS rank_score
        FROM document d
        WHERE d.search_vector @@ plainto_tsquery('english', p_query_text)
    ),
    vec_scores AS (
        SELECT 
            hs.document_id,
            (1 - (hs.embedding <=> p_query_vector))::FLOAT AS sim_score
        FROM handwriting_sample hs
    )
    SELECT 
        d.document_id,
        d.title,
        COALESCE(f.rank_score, 0.0) AS fts_rank,
        COALESCE(v.sim_score, 0.0) AS vector_similarity,
        (p_alpha * COALESCE(f.rank_score, 0.0) + (1.0 - p_alpha) * COALESCE(v.sim_score, 0.0)) AS hybrid_score
    FROM document d
    LEFT JOIN fts_scores f ON d.document_id = f.document_id
    LEFT JOIN vec_scores v ON d.document_id = v.document_id
    ORDER BY hybrid_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

