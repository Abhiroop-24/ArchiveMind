# MINI PROJECT REPORT
## ON
# ARCHIVEMIND: A HYBRID SQL-VECTOR SEMANTIC SEARCH ENGINE FOR DIGITIZED DOCUMENT REPOSITORIES

**Submitted in partial fulfilment of the requirements for the award of degree of**  
**Bachelor of Technology**  
**in**  
**Computer Science & Engineering**  
**UE23CS351A – DBMS Project**

---

### Submitted by:
| Student Name | SRN / Roll No |
| :--- | :--- |
| **A Sheiman Joshi** | **PES2UG24CS003** |
| **Abhiroop** | **PES2UG24CS024** |

---

### Under the Guidance of:
**Demo Teacher**  
*Assistant Professor*  
Department of Computer Science and Engineering  
PES University, Electronic City Campus, Bengaluru – 560 100  

**AUG - DEC 2026**

---

**DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING**  
**FACULTY OF ENGINEERING**  
**PES UNIVERSITY**  
*(Established under Karnataka Act No. 16 of 2013)*  
Electronic City, Hosur Road, Bengaluru – 560 100, Karnataka, India  

---

<div style="page-break-after: always;"></div>

## CERTIFICATE

This is to certify that the mini project entitled **"ArchiveMind: A Hybrid SQL-Vector Semantic Search Engine for Digitized Document Repositories"** is a bonafide work carried out by:

| Student Name | SRN |
| :--- | :--- |
| **A Sheiman Joshi** | **PES2UG24CS003** |
| **Abhiroop** | **PES2UG24CS024** |

in partial fulfilment for the completion of fifth semester **DBMS Project (UE23CS351A)** in the Program of Study - *Bachelor of Technology in Computer Science and Engineering* under rules and regulations of PES University, Bengaluru during the period **AUG. 2026 – DEC. 2026**.

It is certified that all corrections / suggestions indicated for internal assessment have been incorporated in the report. The project has been approved as it satisfies the 5th semester academic requirements in respect of project work.

<br><br><br>
______________________________________  
**Demo Teacher**  
*Assistant Professor & Project Guide*  
Department of Computer Science and Engineering  
PES University, Bengaluru  

---

<div style="page-break-after: always;"></div>

## DECLARATION

We hereby declare that the DBMS Project entitled **"ArchiveMind: A Hybrid SQL-Vector Semantic Search Engine for Digitized Document Repositories"** has been carried out by us under the guidance of **Demo Teacher**, Assistant Professor, and submitted in partial fulfilment of the course requirements for the award of degree of *Bachelor of Technology in Computer Science and Engineering* of PES University, Bengaluru during the academic semester **AUG – DEC 2026**.

We further declare that this project work has not formed the basis for the award of any other Degree, Diploma, or Certificate in any other University or Institution.

<br>

| Student Name | SRN | Signature |
| :--- | :--- | :--- |
| **A Sheiman Joshi** | **PES2UG24CS003** | ____________________ |
| **Abhiroop** | **PES2UG24CS024** | ____________________ |

---

<div style="page-break-after: always;"></div>

## ACKNOWLEDGEMENT

We would like to express our sincere gratitude to our project guide, **Demo Teacher**, Department of Computer Science and Engineering, PES University, for her continuous guidance, constructive suggestions, and encouragement throughout the development of this UE23CS351A - DBMS Project.

We take this opportunity to thank **Dr. Sandesh B J**, Professor and Chairperson, Department of Computer Science and Engineering, PES University, for all the facilities, academic ecosystem, and support received from the department.

We are deeply grateful to **Prof. Jawahar Doreswamy**, Chancellor – PES University, and **Dr. Suryaprasad J**, Vice-Chancellor – PES University, for providing us with boundless opportunities, technological infrastructure, and learning platforms.

Finally, this DBMS Project could not have been completed without the continual moral support, patience, and encouragement received from our families, faculty members, and peers.

---

<div style="page-break-after: always;"></div>

## ABSTRACT

Historical archives, national manuscript libraries, and university repositories contain millions of handwritten letters, scientific codices, treaties, and historical records. While high-resolution digital scanning preserves physical artifacts against organic decay, researchers face severe information retrieval bottlenecks: conventional relational databases (RDBMS) support precise metadata querying and keyword indexing (B-Tree/GIN indexes) but fail when queries involve conceptual semantics or degraded handwriting; conversely, standalone vector similarity databases excel at neural stroke-pattern retrieval but lack relational integrity, ACID transaction guarantees, multi-table foreign keys, role-based access control, and verifiable audit trails.

**ArchiveMind** addresses this dual limitation by presenting a hybrid SQL-Vector semantic search architecture tailored for digitized document preservation and handwriting forensics. The system couples a structured relational schema in PostgreSQL (or embedded SQLite with FTS5 virtual tables) with high-dimensional vector embeddings extracted via forensic stroke analysis. A dedicated digital preservation ingestion station computes cryptographic SHA-256 integrity checksums, extracts OCR transcripts, and registers dense 128-dimensional handwriting feature vectors within ACID transactions.

The database incorporates:
1. **Hybrid Retrieval**: Combines SQL Full-Text Search (tsvector / FTS5) with cosine vector distance scoring via convex combination ($Score = \alpha \cdot FTS + (1-\alpha) \cdot Cosine$).
2. **Chain of Custody Triggers**: Automatically records every document inspection into an immutable view audit table (`DOCUMENT_VIEW`) capturing timestamp, user ID, and IP address.
3. **Automated Citation Triggers**: Automatically fires a database trigger upon scholarly citation creation, logging immutable chain-of-custody provenance attributed to the active researcher.
4. **Role-Based Access Control (RBAC)**: Enforces role isolation between Head Archivists (with DDL/DML mutation privileges) and Academic Researchers (with read-only inspection, citation generation, and analytical access).
5. **Graph Provenance Traversal**: Connects historical persons, multi-archive collections, and viewing chains.

The project demonstrates all fundamental relational operations: complex grouping aggregations, data modifications, cascading integrity deletes, correlated subqueries, and nested subqueries, wrapped within an intuitive, role-based archival management dashboard.

---

<div style="page-break-after: always;"></div>

## TABLE OF CONTENTS

| Chapter No. | Title | Page No. |
| :--- | :--- | :--- |
| **1** | **INTRODUCTION** | **1** |
| | 1.1 Background & Context | 1 |
| | 1.2 Motivation | 1 |
| | 1.3 Scope of the Project | 2 |
| | 1.4 System Architecture Overview | 2 |
| **2** | **PROBLEM DEFINITION** | **3** |
| | 2.1 Limitations of Existing Systems | 3 |
| | 2.2 Proposed Solution | 4 |
| | 2.3 User Roles and Privileges | 4 |
| **3** | **ER MODEL** | **5** |
| | 3.1 Entity Identification and Attributes | 5 |
| | 3.2 Relationships and Cardinality Ratios | 6 |
| | 3.3 Complete ER Diagram | 7 |
| **4** | **ER TO RELATIONAL MAPPING** | **8** |
| | 4.1 Steps of Algorithm for Chosen Problem | 8 |
| | 4.2 Complete Diagram of Relational Mapping (Schema) | 10 |
| **5** | **DDL STATEMENTS** | **11** |
| | 5.1 Relational Table Definitions | 11 |
| | 5.2 Key Constraints & Referential Integrity | 15 |
| | 5.3 Virtual Tables & Index Creation | 16 |
| **6** | **DML STATEMENTS** | **17** |
| | 6.1 Sample Data Insertion (Roles & Users) | 17 |
| | 6.2 Archival Repositories & Collections | 18 |
| | 6.3 Historical Figures & Manuscripts | 19 |
| | 6.4 Vector Handwriting & View Audit Seed Records | 21 |
| **7** | **QUERIES** | **23** |
| | 7.1 Simple Query with GROUP BY & Aggregate | 23 |
| | 7.2 UPDATE Operation | 25 |
| | 7.3 DELETE Operation | 26 |
| | 7.4 Correlated Query | 27 |
| | 7.5 Nested Query | 28 |
| | 7.6 Multi-Table Join & Provenance Query | 29 |
| **8** | **STORED PROCEDURES, FUNCTIONS AND TRIGGERS** | **30** |
| | 8.1 Stored Procedures & Functions | 30 |
| | 8.2 Database Triggers | 33 |
| **9** | **FRONT END DEVELOPMENT** | **35** |
| | 9.1 Technology Stack | 35 |
| | 9.2 Interface Architecture & User Workflows | 35 |
| | 9.3 System Screen Representations | 37 |
| **REFERENCES / BIBLIOGRAPHY** | | **39** |
| **APPENDIX A: DEFINITIONS, ACRONYMS AND ABBREVIATIONS** | | **40** |

---

<div style="page-break-after: always;"></div>

# CHAPTER 1: INTRODUCTION

## 1.1 Background & Context
Historical preservation organizations, including universities, national archives, and manuscript museums, hold vast cultural assets in handwritten form. Prominent examples include draft scientific treatises by Sir Isaac Newton, anatomical and mechanical codices by Leonardo da Vinci, mathematical folios by Srinivasa Ramanujan, and wartime cryptanalytic memos by Alan Turing. In recent years, digitization initiatives have transitioned physical collections to digital image formats (TIFF/JPEG). 

However, photographic digitization alone is insufficient for serious scholarship. Researchers require deep searchability that bridges exact keyword matching with semantic conceptual similarity and visual handwriting forensics.

## 1.2 Motivation
A classic Relational Database Management System (RDBMS) like PostgreSQL provides robust transactional reliability (ACID), referential integrity through foreign keys, and performant B-Tree/GIN indexing for exact string queries. However, pure SQL databases falter when searching noisy historical optical character recognition (OCR) texts or when matching visual handwriting stroke styles across anonymous manuscripts.

Conversely, contemporary Vector Databases (such as Qdrant or Milvus) store neural embeddings and compute fast nearest-neighbor lookups, but they lack relational constraints, foreign keys, complex aggregation functions, multi-table joins, and granular transaction controls.

**ArchiveMind** addresses this gap by synthesizing SQL relational rigor with dense vector similarity search into a unified hybrid DBMS engine.

## 1.3 Scope of the Project
The scope of ArchiveMind encompasses:
1. Designing a fully normalized (3NF/BCNF) relational schema representing archives, collections, manuscripts, authors, access control, citations, and audit records.
2. Ingesting digitized document records through an edge scanning pipeline featuring SHA-256 checksums and OCR extraction.
3. Providing hybrid query execution: combining Full-Text Search rank with cosine vector similarity on 128-dimensional handwriting feature embeddings.
4. Implementing database-level triggers to guarantee an immutable chain-of-custody audit log for every accessed manuscript.
5. Implementing stored procedures to generate standardized academic citations (Chicago, MLA, APA).
6. Executing all five syllabus-mandated DBMS evaluation queries with live verification.
7. Delivering a full-stack, responsive web interface catering to Head Archivists, Researchers, and Digitization Technicians.

## 1.4 System Architecture Overview
The system architecture follows a three-tier design:
* **Preservation & Ingestion Layer**: High-resolution document preservation pipeline equipped with automated document boundary detection, cryptographic SHA-256 checksum calculation, and dense 128-dimensional handwriting feature vector extraction.
* **Database & Hybrid Engine Layer**: Relational database (PostgreSQL 15+ / SQLite FTS5) managing structured entities, integrated with a vector similarity module computing cosine distance across dense embeddings and automated chain-of-custody triggers.
* **Application & Presentation Layer**: FastAPI RESTful backend coupled with a responsive monochrome brutalist frontend featuring interactive hybrid search sliders, manuscript inspection, provenance graph visualization, active role switcher, and an interactive SQL sandbox.

---

<div style="page-break-after: always;"></div>

# CHAPTER 2: PROBLEM DEFINITION

## 2.1 Limitations of Existing Systems
1. **Keyword Brittleness in Historical Documents**: Historical manuscripts frequently suffer from physical decay, faded inks, archaic orthography (e.g., Latin or early modern English), and OCR transcription errors. Pure SQL `LIKE` or basic equality queries return zero hits if the spelling deviates by even a single character.
2. **Absence of Visual Handwriting Forensics in Relational Databases**: Classical databases have no native concept of pen stroke velocity, slant, curvature, or scribe attribution. When an unsigned manuscript is discovered, archivists cannot query: *"Find documents whose penmanship matches Leonardo da Vinci's mirror script with confidence > 85%"*.
3. **Absence of Relational Guarantees in Pure Vector DBs**: Standalone vector engines cannot enforce foreign key cascades, ensure atomic transfers between collections, compute multi-table aggregations (e.g., `COUNT`, `GROUP BY`), or enforce strict role-based access permissions.

## 2.2 Proposed Solution
ArchiveMind provides a **Hybrid SQL-Vector Engine**:
* Relational tables maintain institutional provenance, custodial history, collection hierarchies, document metadata, and access permissions.
* A specialized virtual table / full-text index indexes OCR transcripts.
* A vector table stores dense 128-dimensional handwriting feature embeddings extracted from stroke contour moments.
* A hybrid scoring function fuses textual and vector ranks:
  $$\text{HybridScore} = \alpha \cdot \text{Score}_{\text{FTS}} + (1 - \alpha) \cdot \text{Similarity}_{\text{Cosine}}$$
  where $\alpha \in [0, 1]$ allows researchers to dynamically weight keyword precision against handwriting similarity.

## 2.3 User Roles and Privileges
ArchiveMind implements distinct security roles managed in the `ROLE` and `ACCESS_PERMISSION` tables with backend Role-Based Access Control (RBAC):
* **Head Archivist (Faculty Guide / Demo Teacher)**: Full administrative access; can ingest and preserve collections, modify document statuses, execute database mutation operations (UPDATE/DELETE), and inspect comprehensive security audit logs.
* **Academic Researchers (Abhiroop & A Sheiman Joshi)**: Analytical search and inspection privileges; can execute hybrid searches, inspect OCR texts, generate scholarly citations (which automatically fire database triggers logged under their respective identity), and explore provenance graphs. Blocked by RBAC from executing unauthorized database write mutations (UPDATE/DELETE queries).
* **Digitization Technician**: Ingestion access; permitted to upload scanned documents, compute checksums, and trigger OCR extraction pipelines.
* **Auditor**: Read-only oversight of the chain-of-custody immutable logs in `DOCUMENT_VIEW`.

---

<div style="page-break-after: always;"></div>

# CHAPTER 3: ER MODEL

## 3.1 Entity Identification and Attributes
Based on institutional archival requirements, the system identifies eleven core entities:

1. **ROLE**: Defines system permission levels.
   * `role_id` (PK, Integer)
   * `role_name` (VARCHAR, Unique: 'Head Archivist', 'Researcher', 'Digitization Tech', 'Auditor')

2. **APP_USER**: Authenticated operators of the archive.
   * `user_id` (PK, Integer)
   * `role_id` (FK referencing ROLE)
   * `username` (VARCHAR, Unique)
   * `password_hash` (VARCHAR)
   * `full_name` (VARCHAR)
   * `email` (VARCHAR, Unique)
   * `created_at` (Timestamp)

3. **ARCHIVE**: Physical institutions housing collections.
   * `archive_id` (PK, Integer)
   * `name` (VARCHAR)
   * `location` (VARCHAR)
   * `institution` (VARCHAR)

4. **COLLECTION**: Curated grouping of related manuscripts.
   * `collection_id` (PK, Integer)
   * `archive_id` (FK referencing ARCHIVE)
   * `name` (VARCHAR)
   * `era` (VARCHAR)
   * `description` (TEXT)

5. **ACCESS_PERMISSION**: Granular security mapping between users and collections.
   * `permission_id` (PK, Integer)
   * `user_id` (FK referencing APP_USER)
   * `collection_id` (FK referencing COLLECTION)
   * `permission_type` (VARCHAR: 'READ', 'WRITE', 'ADMIN')
   * `granted_at` (Timestamp)

6. **DOCUMENT**: The primary digital preservation record.
   * `document_id` (PK, Integer)
   * `collection_id` (FK referencing COLLECTION)
   * `digitized_by` (FK referencing APP_USER)
   * `title` (VARCHAR)
   * `doc_type` (VARCHAR: 'Manuscript', 'Letter', 'Decree', 'Mathematical Treatise', 'Notebook', 'Map')
   * `date_written` (VARCHAR)
   * `ocr_text_cache` (TEXT)
   * `search_vector` (tsvector / FTS representation)
   * `checksum_value` (VARCHAR(64), SHA-256 hash)
   * `checksum_algorithm` (VARCHAR)
   * `physical_condition` (VARCHAR: 'Pristine', 'Good', 'Fragile', 'Critical-Decay')
   * `language` (VARCHAR)
   * `image_path` (VARCHAR)
   * `ocr_status` (VARCHAR)
   * `digitized_at` (Timestamp)

7. **PERSON**: Historical figures, authors, scribes, or recipients.
   * `person_id` (PK, Integer)
   * `full_name` (VARCHAR)
   * `birth_year` (Integer)
   * `death_year` (Integer)
   * `biography` (TEXT)

8. **DOCUMENT_AUTHOR**: Associative entity resolving M:N relationship between Documents and Persons.
   * `document_id` (FK referencing DOCUMENT)
   * `person_id` (FK referencing PERSON)
   * `attribution_type` (VARCHAR: 'Author', 'Scribe', 'Signatory', 'Recipient')
   * `confidence_score` (NUMERIC(3,2), e.g., 1.00)
   * Composite PK: `(document_id, person_id)`

9. **HANDWRITING_SAMPLE**: High-dimensional vector features extracted from penmanship.
   * `sample_id` (PK, Integer)
   * `document_id` (FK referencing DOCUMENT)
   * `vector_id` (VARCHAR)
   * `embedding` (Dense 128-d floating point vector)
   * `extraction_method` (VARCHAR)
   * `extracted_at` (Timestamp)

10. **DOCUMENT_VIEW**: Audit log table maintaining legal chain of custody.
    * `view_id` (PK, Integer)
    * `document_id` (FK referencing DOCUMENT)
    * `user_id` (FK referencing APP_USER)
    * `viewed_at` (Timestamp)
    * `ip_address` (VARCHAR)

11. **CITATION**: Automated academic citation records.
    * `citation_id` (PK, Integer)
    * `document_id` (FK referencing DOCUMENT)
    * `citation_text` (TEXT)
    * `citation_style` (VARCHAR: 'Chicago-Archival', 'MLA', 'APA')
    * `generated_at` (Timestamp)

## 3.2 Relationships and Cardinality Ratios
* **ROLE has APP_USER** (1 : N): One role can be held by multiple users; each user has exactly one role.
* **ARCHIVE contains COLLECTION** (1 : N): An archive houses multiple collections; each collection resides in one archive.
* **COLLECTION contains DOCUMENT** (1 : N): A collection holds multiple documents; each document belongs to one collection.
* **APP_USER digitizes DOCUMENT** (1 : N): A technician digitizes multiple documents; each document records its digitizer.
* **DOCUMENT authored by PERSON** (M : N): A document may have multiple contributors/authors; a person may author multiple documents. Mapped via associative table `DOCUMENT_AUTHOR`.
* **DOCUMENT has HANDWRITING_SAMPLE** (1 : N): A document yields one or more extracted vector handwriting samples.
* **DOCUMENT viewed in DOCUMENT_VIEW** (1 : N): Accessing a document creates immutable audit entries.
* **DOCUMENT generates CITATION** (1 : N): Citations in multiple styles can be generated for a document.
* **APP_USER grants ACCESS_PERMISSION on COLLECTION** (M : N): A user can hold permissions across multiple collections.

## 3.3 Complete ER Diagram
```
  +------------------+         1 : N         +-------------------+
  |       ROLE       | <-------------------  |     APP_USER      |
  +------------------+                       +-------------------+
                                                       | 1
                                                       |
                                                       | digitizes (1 : N)
                                                       v
  +------------------+         1 : N         +-------------------+
  |     ARCHIVE      | ------------------->  |    COLLECTION     |
  +------------------+                       +-------------------+
                                                       | 1
                                                       | contains (1 : N)
                                                       v
+--------------------+         M : N         +-------------------+
|       PERSON       | <==================>  |     DOCUMENT      |
+--------------------+  (DOCUMENT_AUTHOR)    +-------------------+
                                               |       |       |
                                         1 : N | 1 : N | 1 : N |
                                               v       v       v
                            +--------------------+ +-------+ +--------------------+
                            | HANDWRITING_SAMPLE | | VIEW  | |      CITATION      |
                            +--------------------+ +-------+ +--------------------+
```

---

<div style="page-break-after: always;"></div>

# CHAPTER 4: ER TO RELATIONAL MAPPING

## 4.1 Steps of Algorithm for Chosen Problem

### Step 1: Mapping Regular (Strong) Entity Types
Create a relational relation for each regular entity, choosing one attribute as the primary key.
* **ROLE**: `(role_id [PK], role_name)`
* **ARCHIVE**: `(archive_id [PK], name, location, institution)`
* **PERSON**: `(person_id [PK], full_name, birth_year, death_year, biography)`

### Step 2: Mapping Weak Entity Types
There are no weak entities without a partial key; all entities contain independent surrogate identifiers.

### Step 3: Mapping 1:1 Binary Relationship Types
Not applicable in this schema.

### Step 4: Mapping 1:N Binary Relationship Types
For each 1:N relationship, include the primary key of the "1" side as a foreign key attribute in the relation representing the "N" side:
* **APP_USER**: Include `role_id [FK]` referencing `ROLE(role_id)`.
* **COLLECTION**: Include `archive_id [FK]` referencing `ARCHIVE(archive_id)`.
* **DOCUMENT**: Include `collection_id [FK]` referencing `COLLECTION(collection_id)` and `digitized_by [FK]` referencing `APP_USER(user_id)`.
* **HANDWRITING_SAMPLE**: Include `document_id [FK]` referencing `DOCUMENT(document_id)`.
* **DOCUMENT_VIEW**: Include `document_id [FK]` referencing `DOCUMENT(document_id)` and `user_id [FK]` referencing `APP_USER(user_id)`.
* **CITATION**: Include `document_id [FK]` referencing `DOCUMENT(document_id)`.

### Step 5: Mapping M:N Binary Relationship Types
Create a new associative relation with foreign keys referencing the primary keys of both participating entity types. The combination of these foreign keys forms the composite primary key:
* **DOCUMENT_AUTHOR**: `(document_id [FK], person_id [FK], attribution_type, confidence_score)`. Primary Key is `(document_id, person_id)`.
* **ACCESS_PERMISSION**: `(permission_id [PK], user_id [FK], collection_id [FK], permission_type, granted_at)` with unique constraint on `(user_id, collection_id)`.

### Step 6: Mapping Multivalued Attributes
Not applicable; all attributes are atomic and normalized to First Normal Form (1NF).

### Step 7: Mapping N-ary Relationships
All relationships in ArchiveMind are binary.

## 4.2 Complete Diagram of Relational Mapping (Schema)
* **ROLE** (<ins>role_id</ins>, role_name)
* **APP_USER** (<ins>user_id</ins>, username, password_hash, full_name, email, created_at, *role_id*)
  * *role_id* $\rightarrow$ **ROLE**(role_id)
* **ARCHIVE** (<ins>archive_id</ins>, name, location, institution)
* **COLLECTION** (<ins>collection_id</ins>, name, era, description, *archive_id*)
  * *archive_id* $\rightarrow$ **ARCHIVE**(archive_id)
* **ACCESS_PERMISSION** (<ins>permission_id</ins>, permission_type, granted_at, *user_id*, *collection_id*)
  * *user_id* $\rightarrow$ **APP_USER**(user_id)
  * *collection_id* $\rightarrow$ **COLLECTION**(collection_id)
* **DOCUMENT** (<ins>document_id</ins>, title, doc_type, date_written, ocr_text_cache, checksum_value, checksum_algorithm, physical_condition, language, image_path, ocr_status, digitized_at, *collection_id*, *digitized_by*)
  * *collection_id* $\rightarrow$ **COLLECTION**(collection_id)
  * *digitized_by* $\rightarrow$ **APP_USER**(user_id)
* **PERSON** (<ins>person_id</ins>, full_name, birth_year, death_year, biography)
* **DOCUMENT_AUTHOR** (<ins>*document_id*, *person_id*</ins>, attribution_type, confidence_score)
  * *document_id* $\rightarrow$ **DOCUMENT**(document_id)
  * *person_id* $\rightarrow$ **PERSON**(person_id)
* **HANDWRITING_SAMPLE** (<ins>sample_id</ins>, vector_id, embedding, extraction_method, extracted_at, *document_id*)
  * *document_id* $\rightarrow$ **DOCUMENT**(document_id)
* **DOCUMENT_VIEW** (<ins>view_id</ins>, viewed_at, ip_address, *document_id*, *user_id*)
  * *document_id* $\rightarrow$ **DOCUMENT**(document_id)
  * *user_id* $\rightarrow$ **APP_USER**(user_id)
* **CITATION** (<ins>citation_id</ins>, citation_text, citation_style, generated_at, *document_id*)
  * *document_id* $\rightarrow$ **DOCUMENT**(document_id)

---

<div style="page-break-after: always;"></div>

# CHAPTER 5: DDL STATEMENTS

The following Data Definition Language (DDL) statements define the relational database structure:

```sql
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

-- 5. ACCESS_PERMISSION TABLE
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
    search_vector tsvector,
    checksum_value VARCHAR(64) NOT NULL,
    checksum_algorithm VARCHAR(20) DEFAULT 'SHA-256',
    physical_condition VARCHAR(30) CHECK (physical_condition IN ('Pristine', 'Good', 'Fragile', 'Critical-Decay')),
    language VARCHAR(50) DEFAULT 'English',
    image_path VARCHAR(500) NOT NULL,
    ocr_status VARCHAR(20) DEFAULT 'COMPLETED' CHECK (ocr_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    digitized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. PERSON TABLE
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

-- 9. HANDWRITING_SAMPLE TABLE
CREATE TABLE handwriting_sample (
    sample_id SERIAL PRIMARY KEY,
    document_id INT NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
    vector_id VARCHAR(64) NOT NULL,
    embedding vector(128),
    extraction_method VARCHAR(50) DEFAULT 'ResNet50-Forensic-Extractor',
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. DOCUMENT_VIEW TABLE (Audit Trail)
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
```

---

<div style="page-break-after: always;"></div>

# CHAPTER 6: DML STATEMENTS

Below are representative Data Manipulation Language (DML) insert statements populating the database with realistic archival records:

```sql
-- Roles
INSERT INTO role (role_id, role_name) VALUES
(1, 'Head Archivist'), (2, 'Researcher'), (3, 'Digitization Tech'), (4, 'Auditor');

-- Users
INSERT INTO app_user (user_id, role_id, username, password_hash, full_name, email) VALUES
(1, 1, 'demo_teacher', 'pbkdf2:sha256:archivist_hash_99', 'Demo Teacher', 'demo.teacher@pes.edu'),
(2, 2, 'sheiman_j', 'pbkdf2:sha256:researcher_hash_01', 'A Sheiman Joshi', 'sheiman.pes2ug24cs003@pes.edu'),
(3, 2, 'abhiroop_r', 'pbkdf2:sha256:researcher_hash_02', 'Abhiroop', 'abhiroop.pes2ug24cs024@pes.edu'),
(4, 3, 'preservation_tech', 'pbkdf2:sha256:tech_hash_44', 'Preservation Station Tech', 'digitization.tech@pes.edu'),
(5, 4, 'auditor_compliance', 'pbkdf2:sha256:audit_hash_12', 'Archive Compliance Officer', 'audit@pes.edu');

-- Archives & Collections
INSERT INTO archive (archive_id, name, location, institution) VALUES
(1, 'Cambridge Digital Archives', 'Cambridge, UK', 'Cambridge University Library'),
(2, 'Vatican Apostolic Manuscript Repository', 'Vatican City', 'Vatican Apostolic Library'),
(3, 'National Archives of India Special Collections', 'New Delhi, India', 'National Archives of India'),
(4, 'Bletchley Park Historical Records', 'Milton Keynes, UK', 'Bletchley Park Trust');

INSERT INTO collection (collection_id, archive_id, name, era, description) VALUES
(1, 1, 'Newtonian Scientific Manuscripts', 'Enlightenment (1680-1720)', 'Original handwritten treatises and mathematical notebooks of Sir Isaac Newton.'),
(2, 2, 'Da Vinci Codex & Anatomy Studies', 'Renaissance (1480-1519)', 'Mirror-handwriting sketch folios exploring mechanics and hydraulic engineering.'),
(3, 3, 'Ramanujan Lost Notebook & Letter Folios', 'Modern Mathematics (1910-1920)', 'Formulae on mock theta functions and partition theory.'),
(4, 4, 'Turing Decryption & Computing Dispatches', 'World War II (1939-1950)', 'Bletchley Park Hut 8 cryptanalysis memos and AI papers.'),
(5, 1, 'Victorian Analytical Engine Papers', 'Victorian Era (1840-1860)', 'Notes by Ada Lovelace and Charles Babbage detailing computational algorithms.');

-- Authors
INSERT INTO person (person_id, full_name, birth_year, death_year, biography) VALUES
(1, 'Sir Isaac Newton', 1642, 1727, 'English polymath active as mathematician and physicist.'),
(2, 'Leonardo da Vinci', 1452, 1519, 'Italian polymath of the High Renaissance known for mirror script.'),
(3, 'Srinivasa Ramanujan', 1887, 1920, 'Legendary Indian mathematician who contributed to mock theta functions.'),
(4, 'Alan Turing', 1912, 1954, 'English mathematician, computer scientist and codebreaker.'),
(5, 'Ada Lovelace', 1815, 1852, 'Mathematician recognized as the first computer programmer.');

-- Documents
INSERT INTO document (document_id, collection_id, digitized_by, title, doc_type, date_written, ocr_text_cache, checksum_value, physical_condition, language, image_path, ocr_status) VALUES
(1, 1, 3, 'Philosophiae Naturalis Principia Mathematica - Draft Folio 12', 'Manuscript', '1687', 'Lex I: Corpus omne perseverare in statu suo quiescendi vel movendi uniformiter in directum. The forces acting upon celestial bodies obey inverse square law of universal gravitation.', 'a3f8c149b18361bdfa3490192e21bbd83921048209849208a3821092830192ab', 'Good', 'Latin', 'newton_principia_f12.jpg', 'COMPLETED'),
(3, 2, 3, 'Codex Atlanticus: Folio 104v on Aerial Screws and Vortex Fluid Dynamics', 'Notebook', '1489', 'La vite aerea: When turned with swiftness, this helical screw made of starched linen will spiral upwards into the air. Water vortices mirror air currents.', '7d3298a4bc102938401928301928301928301928301928301928301928301928', 'Pristine', 'Italian (Mirror-Script)', 'davinci_codex_104v.jpg', 'COMPLETED'),
(5, 3, 3, 'Mock Theta Functions - Final Letter to G.H. Hardy from Madras', 'Letter', '1920-01-12', 'I am extremely sorry for not writing you a single letter up to now. I have discovered very interesting functions recently which I call Mock Theta functions.', 'f12089acbd019283019283019283019283019283019283019283019283019283', 'Fragile', 'English', 'ramanujan_letter_hardy.jpg', 'COMPLETED'),
(7, 4, 3, 'Hut 8 Cryptanalysis Memo on Enigma Naval 4-Rotor Wirings', 'Letter', '1941-11-04', 'Banburismus techniques allow reduction of rotor wheel combinations. The Bombe decryption machinery requires synchronized menu configuration for Offizier messages.', 'd449102830192830192830192830192830192830192830192830192830192830', 'Pristine', 'English', 'turing_hut8_memo.jpg', 'COMPLETED'),
(9, 5, 3, 'Notes on the Analytical Engine: Note G - Bernoulli Number Computation', 'Manuscript', '1843', 'Note G describes the sequence of operations for calculating Numbers of Bernoulli. The Analytical Engine weaves algebraic patterns just as Jacquard loom weaves flowers.', '3391028301928301928301928301928301928301928301928301928301928301', 'Good', 'English/French', 'lovelace_note_g_bernoulli.jpg', 'COMPLETED');
```

---

<div style="page-break-after: always;"></div>

# CHAPTER 7: QUERIES

This chapter presents the execution of the mandatory queries specified in the UE23CS351A evaluation criteria.

## 7.1 Simple Query with GROUP BY & AGGREGATE
**Objective**: Aggregate preserved manuscripts across historical eras and physical preservation conditions, computing total counts, average OCR transcript character length, and earliest/latest dates.

```sql
SELECT 
    c.era,
    d.physical_condition,
    COUNT(d.document_id) AS total_manuscripts,
    ROUND(AVG(LENGTH(d.ocr_text_cache)), 2) AS avg_ocr_length,
    MIN(d.date_written) AS oldest_record,
    MAX(d.date_written) AS newest_record
FROM document d
JOIN collection c ON d.collection_id = c.collection_id
GROUP BY c.era, d.physical_condition
ORDER BY c.era ASC, total_manuscripts DESC;
```

**Output**:
| era | physical_condition | total_manuscripts | avg_ocr_length | oldest_record | newest_record |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Enlightenment (1680-1720) | Fragile | 1 | 185.00 | 1704 | 1704 |
| Enlightenment (1680-1720) | Good | 1 | 243.00 | 1687 | 1687 |
| Modern Mathematics (1910-1920) | Critical-Decay | 1 | 188.00 | 1919 | 1919 |
| Modern Mathematics (1910-1920) | Fragile | 1 | 208.00 | 1920-01-12 | 1920-01-12 |
| Renaissance (1480-1519) | Good | 1 | 207.00 | 1510 | 1510 |
| Renaissance (1480-1519) | Pristine | 1 | 174.00 | 1489 | 1489 |
| Victorian Era (1840-1860) | Fragile | 1 | 195.00 | 1834 | 1834 |
| Victorian Era (1840-1860) | Good | 1 | 204.00 | 1843 | 1843 |
| World War II (1939-1950) | Good | 1 | 205.00 | 1950 | 1950 |
| World War II (1939-1950) | Pristine | 1 | 207.00 | 1941-11-04 | 1941-11-04 |

---

## 7.2 UPDATE Operation
**Objective**: Update physical preservation condition to `'Good'` and mark OCR processing to `'COMPLETED'` for manuscripts previously flagged as `'Critical-Decay'`.

```sql
UPDATE document
SET physical_condition = 'Good',
    ocr_status = 'COMPLETED'
WHERE physical_condition = 'Critical-Decay';
```

**Verification Query**:
```sql
SELECT document_id, title, physical_condition, ocr_status 
FROM document 
WHERE document_id = 6;
```

**Output**:
| document_id | title | physical_condition | ocr_status |
| :--- | :--- | :--- | :--- |
| 6 | Lost Notebook: Modular Equations and Asymptotic Partitions Folio 34 | Good | COMPLETED |

*(1 row affected, condition successfully transitioned)*

---

## 7.3 DELETE Operation
**Objective**: Safely scrub temporary diagnostic inspection view entries without compromising the permanent audit trail.

```sql
DELETE FROM document_view
WHERE ip_address LIKE '%[TEMP]%' OR view_id > 1000;
```

**Output**:
```
Query executed successfully. 0 rows deleted (database contains strictly certified IP audit events).
Verification: Remaining active audit trail records = 6.
```

---

## 7.4 Correlated Subquery
**Objective**: Retrieve all documents whose OCR character length strictly exceeds the average OCR character length of documents residing within their **SAME** collection.

```sql
SELECT 
    d1.document_id,
    d1.title,
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
```

**Output**:
| document_id | title | collection_name | doc_char_length |
| :--- | :--- | :--- | :--- |
| 1 | Philosophiae Naturalis Principia Mathematica - Draft Folio 12 | Newtonian Scientific Manuscripts | 243 |
| 4 | Anatomical Study: Musculature and Tendons of the Human Arm | Da Vinci Codex & Anatomy Studies | 207 |
| 5 | Mock Theta Functions - Final Letter to G.H. Hardy from Madras | Ramanujan Lost Notebook & Letter Folios | 208 |
| 7 | Hut 8 Cryptanalysis Memo on Enigma Naval 4-Rotor Wirings | Turing Decryption & Computing Dispatches | 207 |
| 9 | Notes on the Analytical Engine: Note G - Bernoulli Number Computation | Victorian Analytical Engine Papers | 204 |

*Explanation*: For each candidate document $d_1$, the inner subquery evaluates the dynamic average character count of documents having $d_2.\text{collection\_id} = d_1.\text{collection\_id}$. Only documents surpassing their specific collection average are selected.

---

## 7.5 Nested Subquery
**Objective**: Identify all historical authors whose digitized manuscripts reside in archives that curate two or more distinct collections.

```sql
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
```

**Output**:
| person_id | full_name | birth_year | death_year | authored_document_count |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Sir Isaac Newton | 1642 | 1727 | 2 |
| 5 | Ada Lovelace | 1815 | 1852 | 1 |
| 6 | Charles Babbage | 1791 | 1871 | 2 |

*Explanation*: The deepest subquery finds archive IDs managing $\ge 2$ collections (Cambridge Digital Archives). The intermediate query selects all document IDs belonging to collections in those archives. The outer query matches contributing persons and computes their authored count.

---

<div style="page-break-after: always;"></div>

# CHAPTER 8: STORED PROCEDURES, FUNCTIONS AND TRIGGERS

## 8.1 Stored Procedures & Functions

### 1. Stored Procedure: `sp_generate_archival_citation`
Formats academic citations adhering to Chicago, MLA, or APA standards and inserts them into the `CITATION` table within a single transaction.

```sql
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

    IF p_style = 'MLA' THEN
        v_citation_text := v_author_name || '. "' || v_title || '." ' || v_date || '. ' || v_col_name || ', ' || v_archive_name || '. ArchiveMind Digitized Repository.';
    ELSE
        v_citation_text := v_author_name || ', ' || v_title || ' (' || v_date || '), ' || v_col_name || ', ' || v_archive_name || '. Digitized preservation record.';
    END IF;

    INSERT INTO citation (document_id, citation_text, citation_style, generated_at)
    VALUES (p_document_id, v_citation_text, p_style, CURRENT_TIMESTAMP);
    
    COMMIT;
END;
$$;
```

---

## 8.2 Database Triggers

### 1. Trigger: Full-Text Search Vector Generator
Synchronizes the weighted `search_vector` column automatically whenever document titles or OCR transcripts are added or modified:

```sql
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
```

### 2. Trigger: Cryptographic Checksum Integrity Enforcer
Guarantees that no manuscript can be updated with an invalid or corrupted cryptographic hash:

```sql
CREATE OR REPLACE FUNCTION fn_verify_document_integrity()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.checksum_value IS NULL OR length(NEW.checksum_value) < 32 THEN
        RAISE EXCEPTION 'Integrity Error: Cryptographic checksum is invalid or truncated.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_verify_integrity
BEFORE UPDATE ON document
FOR EACH ROW
EXECUTE FUNCTION fn_verify_document_integrity();
```

### 3. Trigger: Automated Citation Generation Audit Logging
Guarantees an immutable chain-of-custody audit record in `DOCUMENT_VIEW` whenever an academic citation is registered:

```sql
-- PostgreSQL Syntax:
CREATE OR REPLACE FUNCTION fn_audit_citation_generation()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO document_view (document_id, user_id, ip_address, viewed_at)
    VALUES (
        NEW.document_id,
        COALESCE(NEW.user_id, 3),
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

-- SQLite Syntax:
CREATE TRIGGER trg_audit_citation_generation
AFTER INSERT ON citation
BEGIN
    INSERT INTO document_view (document_id, user_id, ip_address, viewed_at)
    VALUES (
        NEW.document_id,
        COALESCE(NEW.user_id, 3),
        '127.0.0.1 [TRIGGER:CITATION_' || UPPER(NEW.citation_style) || ']',
        CURRENT_TIMESTAMP
    );
END;
```

---

<div style="page-break-after: always;"></div>

# CHAPTER 9: FRONT END DEVELOPMENT

## 9.1 Technology Stack & Design System
* **Architecture**: Modern Single Page Application (SPA) built using Semantic HTML5, Vanilla JavaScript (ES6+), and Vanilla CSS.
* **Design Aesthetic**: Minimalist monochrome brutalism inspired by the Omarchy Vantablack and Nothing OS design language (pure white backgrounds, stark black structural cards, high-contrast typography, zero-radius rectangular geometry `border-radius: 0px`, and subtle micro-interactions).
* **Typography**: Clean grotesque sans-serif (`Inter`, `Helvetica Neue`) combined with monospaced accents (`Geist Mono`, `JetBrains Mono`) for cryptographic hashes, SQL statements, and metadata tags.
* **Icons & Visualization**: Lucide monochrome iconography and HTML5 Canvas interactive topological network visualizer.
* **Backend Application Server**: Python 3.14, FastAPI REST Framework, Uvicorn ASGI Server.
* **Database**: PostgreSQL / SQLite with FTS5 Virtual Table Indexing, dynamic SQL triggers, and dense 128-dimensional vector cosine matching.

## 9.2 Interface Architecture & User Workflows
The front end provides six major tabbed workflows:
1. **Hybrid Search Dashboard**: Users enter natural language keywords and adjust the **Alpha Fusion Slider** (ranging from 100% Vector to 100% SQL FTS). Result cards display individual FTS ranks, vector similarity scores, and combined hybrid scores.
2. **Manuscript Inspector**: Offers deep forensic review of selected manuscripts, displaying high-resolution metadata, cryptographic SHA-256 hashes, full OCR transcripts, and stored-procedure citation generators.
3. **Provenance Network Visualizer**: Renders an interactive canvas graph displaying relational linkages between Historical Authors, Manuscripts, Archival Collections, Institutions, and View Audit Nodes.
4. **Digital Preservation Ingestion Station**: Form inputs undergo client-server validation, SHA-256 hashing, FTS indexing, and vector extraction within an atomic transaction.
5. **DBMS Evaluation Queries Sandbox**: Provides one-click execution of all 5 mandatory evaluation queries with execution timings, query rationale, and tabular result sets.
6. **Audit & Chain of Custody Trail**: Displays real-time database view triggers and IP addresses verifying security and provenance.
7. **Active Role Switcher (RBAC)**: Allows dynamic switching between **Abhiroop (Researcher)**, **A Sheiman Joshi (Researcher)**, and **Demo Teacher (Head Archivist)**, instantly updating system permissions and attributing audit records.

---

<div style="page-break-after: always;"></div>

# REFERENCES / BIBLIOGRAPHY

1. Elmasri, R., & Navathe, S. B. (2016). *Fundamentals of Database Systems* (7th ed.). Pearson.
2. Silberschatz, A., Korth, H. F., & Sudarshan, S. (2020). *Database System Concepts* (7th ed.). McGraw-Hill Education.
3. PostgreSQL Global Development Group. (2025). *PostgreSQL 16 Documentation: Full Text Search and GiST/GIN Indexing*. https://www.postgresql.org/docs/
4. Johnson, J., Douze, M., & Jégou, H. (2019). Billion-scale similarity search with GPUs. *IEEE Transactions on Big Data*, 7(3), 535-547.
5. Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2022). *Introduction to Algorithms* (4th ed.). MIT Press.

---

<div style="page-break-after: always;"></div>

# APPENDIX A: DEFINITIONS, ACRONYMS AND ABBREVIATIONS

* **ACID**: Atomicity, Consistency, Isolation, Durability
* **API**: Application Programming Interface
* **BCNF**: Boyce-Codd Normal Form
* **DML**: Data Manipulation Language
* **DDL**: Data Definition Language
* **ER**: Entity-Relationship
* **FTS**: Full-Text Search
* **GIN**: Generalized Inverted Index
* **IVFFlat**: Inverted File with Flat Compression (Vector Index)
* **OCR**: Optical Character Recognition
* **PES**: People's Education Society
* **PK / FK**: Primary Key / Foreign Key
* **RRF**: Reciprocal Rank Fusion
* **SHA-256**: Secure Hash Algorithm 256-bit
* **SQL**: Structured Query Language

