# ArchiveMind: Intelligent Document Preservation & Handwriting Forensics
### UE23CS351A – DBMS Project | Department of Computer Science & Engineering | PES University

**Team Members**:  
- **A Sheiman Joshi** (`PES2UG24CS003`)
- **Abhiroop** (`PES2UG24CS024`)  
**Project Guide**: Dr. Shilpa S  

---

## 🏛️ Project Overview
**ArchiveMind** is a hybrid SQL-Vector semantic search engine designed for digitized historical document repositories. It bridges the gap between structured relational data (PostgreSQL 3NF schema, foreign keys, ACID transactions, access permissions) and unstructured AI forensics (Full-Text Search over OCR transcripts, dense 128-dimensional handwriting stroke similarity vectors, and relational provenance graph traversal).

---

## 📁 Repository Structure & Deliverables

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
│   └── index.html                   # Modern responsive Web UI with tabs & Canvas Graph
├── scripts/
│   └── run_demo.sh                  # One-click demo launcher script
├── DEMO_GUIDE.md                    # 5-minute presentation script & viva answers
└── README.md                        # Project overview & instructions
```

---

## ⚡ Quick Start (Run Demo)

```bash
cd /home/sheimanjoshi/.gemini/antigravity/scratch/ArchiveMind
./scripts/run_demo.sh
```

Then open your browser at **`http://localhost:8000`**.

---

## 📄 Academic Project Report & Submission
The complete project report formatted exactly to the PES University template is located in `docs/`:
* Markdown: `docs/ArchiveMind_DBMS_Project_Report.md`
* Printable HTML: Open `docs/ArchiveMind_DBMS_Project_Report.html` in any browser and press **Ctrl+P** (Print $\rightarrow$ Save as PDF).

