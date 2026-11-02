-- ====================================================================
-- ARCHIVEMIND: Evaluation SQL Queries for DBMS Viva & Demo
-- Course: UE23CS351A - DBMS Project | PES University
-- ====================================================================

-- --------------------------------------------------------------------
-- 7.1 SIMPLE QUERY WITH GROUP BY & AGGREGATE
-- Description: Aggregate documents by physical condition and era, 
-- calculating count, average title length, and earliest/latest dates.
-- --------------------------------------------------------------------
SELECT 
    c.era,
    d.physical_condition,
    COUNT(d.document_id) AS total_manuscripts,
    ROUND(AVG(LENGTH(d.ocr_text_cache)), 2) AS avg_ocr_character_length,
    MIN(d.date_written) AS oldest_record_date,
    MAX(d.date_written) AS newest_record_date
FROM document d
JOIN collection c ON d.collection_id = c.collection_id
GROUP BY c.era, d.physical_condition
HAVING COUNT(d.document_id) >= 1
ORDER BY c.era ASC, total_manuscripts DESC;


-- --------------------------------------------------------------------
-- 7.2 UPDATE OPERATION
-- Description: Update physical condition of documents undergoing conservation
-- and mark OCR status to COMPLETED where text cache has been validated.
-- --------------------------------------------------------------------
UPDATE document
SET 
    physical_condition = 'Pristine',
    ocr_status = 'COMPLETED',
    checksum_value = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
WHERE collection_id IN (
    SELECT collection_id 
    FROM collection 
    WHERE name = 'Newtonian Scientific Manuscripts'
) AND physical_condition = 'Fragile';


-- --------------------------------------------------------------------
-- 7.3 DELETE OPERATION
-- Description: Delete temporary view audit entries older than 365 days
-- or associated with obsolete demo sessions while preserving archive documents.
-- --------------------------------------------------------------------
DELETE FROM document_view
WHERE ip_address LIKE '%[TEMP]%' 
   OR viewed_at < CURRENT_TIMESTAMP - INTERVAL '365 days';


-- --------------------------------------------------------------------
-- 7.4 CORRELATED SUBQUERY
-- Description: Retrieve all documents whose OCR character count exceeds
-- the average OCR character count of documents strictly within the SAME collection.
-- --------------------------------------------------------------------
SELECT 
    d1.document_id,
    d1.title,
    d1.collection_id,
    c.name AS collection_name,
    LENGTH(d1.ocr_text_cache) AS doc_char_length
FROM document d1
JOIN collection c ON d1.collection_id = c.collection_id
WHERE LENGTH(d1.ocr_text_cache) > (
    SELECT AVG(LENGTH(d2.ocr_text_cache))
    FROM document d2
    WHERE d2.collection_id = d1.collection_id
)
ORDER BY d1.collection_id, doc_char_length DESC;


-- --------------------------------------------------------------------
-- 7.5 NESTED SUBQUERY
-- Description: Find all historical persons (authors) who have contributed
-- to manuscripts stored in archives that contain more than 2 distinct collections.
-- --------------------------------------------------------------------
SELECT 
    p.person_id,
    p.full_name,
    p.birth_year,
    p.death_year,
    COUNT(da.document_id) AS authored_document_count
FROM person p
JOIN document_author da ON p.person_id = da.person_id
WHERE da.document_id IN (
    SELECT d.document_id
    FROM document d
    WHERE d.collection_id IN (
        SELECT c.collection_id
        FROM collection c
        WHERE c.archive_id IN (
            SELECT a.archive_id
            FROM archive a
            JOIN collection col ON a.archive_id = col.archive_id
            GROUP BY a.archive_id
            HAVING COUNT(col.collection_id) >= 2
        )
    )
)
GROUP BY p.person_id, p.full_name, p.birth_year, p.death_year
ORDER BY authored_document_count DESC;


-- --------------------------------------------------------------------
-- BONUS 7.6: MULTI-TABLE JOIN WITH ATTRIBUTION & ARCHIVE PROVENANCE
-- Description: Traces full chain of custody from individual document
-- to historical author, collection, institution, and viewing history.
-- --------------------------------------------------------------------
SELECT 
    d.document_id,
    d.title AS manuscript_title,
    p.full_name AS primary_author,
    da.attribution_type,
    c.name AS collection_name,
    a.name AS archive_name,
    a.institution,
    COUNT(dv.view_id) AS view_access_count
FROM document d
JOIN collection c ON d.collection_id = c.collection_id
JOIN archive a ON c.archive_id = a.archive_id
LEFT JOIN document_author da ON d.document_id = da.document_id
LEFT JOIN person p ON da.person_id = p.person_id
LEFT JOIN document_view dv ON d.document_id = dv.document_id
GROUP BY d.document_id, d.title, p.full_name, da.attribution_type, c.name, a.name, a.institution
ORDER BY d.document_id ASC;

