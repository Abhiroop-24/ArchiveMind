# ArchiveMind: Intelligent Document Preservation & Handwriting Forensics
### UE23CS351A – DBMS Project | Department of Computer Science & Engineering | PES University

**Team Members**:  
- **A Sheiman Joshi** (`PES2UG24CS003`)
- **Abhiroop** (`PES2UG24CS024`)  
**Project Guide**: Demo Teacher  

---

## Project Overview
**ArchiveMind** is a hybrid SQL-Vector semantic search engine designed for digitized historical document repositories. It bridges the gap between structured relational data (PostgreSQL 3NF schema, foreign keys, ACID transactions, access permissions) and unstructured AI forensics:
- **Full-Text Search (FTS5)**: Fast tokenized keyword matching across OCR transcripts.
- **Dense 128-dimensional Vector Similarity**: Cosine alignment of handwriting stroke features.
- **Relational Provenance Graph**: Interactive topological traversal tracing Author $\rightarrow$ Manuscript $\rightarrow$ Archival Collection $\rightarrow$ Institution $\rightarrow$ Audit Trail.
- **Pure Monochrome Minimalist UI**: Styled in the sleek Omarchy Vantablack theme.

---

## Repository Structure

```
ArchiveMind/
├── backend/
│   └── server.py                    # FastAPI REST Application Server
├── database/
│   ├── db_manager.py                # Database Manager (SQLite FTS5 + Vector Engine)
│   ├── schema_postgres.sql          # Standard PostgreSQL DDL Schema with pgvector
│   ├── dml_seed.sql                 # Historical manuscripts and authors seed dataset
│   ├── queries.sql                  # Evaluation Queries 7.1 to 7.5 for DBMS Lab
│   └── procedures_triggers.sql      # Stored procedures & triggers
├── docs/
│   ├── ArchiveMind_DBMS_Project_Report.md    # Complete academic project report
│   └── ArchiveMind_DBMS_Project_Report.html  # Formatted printable report for PDF export
├── frontend/
│   └── index.html                   # Pure monochrome Omarchy Vantablack UI & Canvas Graph
├── scripts/
│   └── run_demo.sh                  # One-click demo launcher script
├── DEMO_GUIDE.md                    # Presentation script & viva questions/answers
├── requirements.txt                 # Python dependencies
├── run.sh                           # Direct root startup script
└── README.md                        # Documentation and run guide
```

---

## Quick Start & Run Guide

### 1. Prerequisites
- **Python 3.8+** (Tested and compatible with Python 3.8 through Python 3.14+)
- **Git**

### 2. Clone the Repository
```bash
git clone https://github.com/Abhiroop-24/ArchiveMind.git
cd ArchiveMind
```

### 3. Run the Application
You can run the startup script directly:

```bash
chmod +x run.sh
./run.sh
```

*(Alternatively, use `./scripts/run_demo.sh`)*

The script will:
1. Automatically create and activate a Python virtual environment (`venv`).
2. Install all required dependencies (`fastapi`, `uvicorn`, `pydantic`, `python-multipart`).
3. Seed and index the relational database and FTS5 virtual tables.
4. Launch the server at **`http://localhost:8000`**.

### 4. Open in Browser
Open your browser and navigate to:
**`http://localhost:8000`**

---

## Features & Demo Walkthrough

### 1. Hybrid SQL-Vector Search
- Enter search terms like `"gravitation"`, `"imitation game"`, or `"bernoulli"`.
- Adjust the **$\alpha$ fusion slider** to dynamically shift weighting between pure keyword FTS (100% SQL) and handwriting stroke similarity (100% Vector).
- Filter by specific handwriting styles (Isaac Newton, Leonardo da Vinci, Ramanujan, Alan Turing, Ada Lovelace, Charles Babbage).

### 2. Manuscript Inspector & Citation Generator
- Click **Inspect** on any manuscript to view its complete preservation metadata and cryptographic **SHA-256** checksum.
- View full-text OCR transcripts.
- Generate live academic citations in **Chicago**, **MLA**, or **APA** styles via stored procedures.

### 3. Archival Provenance Topology
- Interactive HTML5 Canvas graph tracing the full relational lineage of manuscripts, scholars, collections, and repositories.

### 4. Digital Preservation Ingestion Station
- Ingest new manuscripts into the database within an **ACID transaction**.
- Generates an automated SHA-256 integrity hash, synchronizes the FTS5 virtual index, and extracts a 128-dimensional handwriting feature vector.

### 5. DBMS Evaluation Queries Sandbox (PES Lab Viva)
Execute all 5 mandatory evaluation query types with live execution time benchmarking in milliseconds:
- **7.1 GROUP BY & Aggregation**: Era & condition distribution count.
- **7.2 UPDATE Mutation**: Conservation state & checksum synchronization.
- **7.3 DELETE Operation**: Stale guest audit trail scrubbing.
- **7.4 Correlated Subquery**: Manuscripts above collection average length.
- **7.5 Nested Subquery**: Multi-collection author cross-referencing.

### 6. Audit Trail & Triggers
- Real-time audit log automatically captured through database triggers whenever manuscripts are viewed.

---

## Academic Project Report & Submission
The complete project report formatted to the PES University template is located in `docs/`:
- **Markdown**: `docs/ArchiveMind_DBMS_Project_Report.md`
- **Printable HTML / PDF**: Open `docs/ArchiveMind_DBMS_Project_Report.html` in any browser and press **Ctrl+P** (Print $\rightarrow$ Save as PDF).
- **Viva Preparation**: Refer to `DEMO_GUIDE.md` for a 5-minute presentation script and common viva questions with answers.
