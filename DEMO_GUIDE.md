# ARCHIVEMIND: DEMO PRESENTATION & VIVA GUIDE
### Course: UE23CS351A – DBMS Project | PES University
**Team Members**:
- **A Sheiman Joshi** (`PES2UG24CS003`) — *Database Architecture & Relational Engine*
- **Abhiroop** (`PES2UG24CS024`) — *Vector Embeddings & Search Fusion*  
**Project Guide**: Demo Teacher  

---

## 🚀 1. How to Launch the Demo

From the project root directory (`/home/sheimanjoshi/.gemini/antigravity/scratch/ArchiveMind`), execute:

```bash
./scripts/run_demo.sh
```

Or manually:
```bash
source venv/bin/activate
uvicorn backend.server:app --port 8000 --reload
```

Then open your browser and navigate to:  
👉 **`http://localhost:8000`**

To view the printable **Academic Project Report**:  
Open **`docs/ArchiveMind_DBMS_Project_Report.html`** in any web browser and click **"Print / Save as PDF"**.

---

## ⏱️ 2. The 5-Minute Flawless Presentation Script

When Demo Teacher or the external examiner asks you to demonstrate your project, follow this exact sequence:

### **Minute 1: The Problem & Architecture (The "Hook")**
> *"Good morning ma'am / sir. My project is **ArchiveMind: A Hybrid SQL-Vector Semantic Search Engine for Digitized Document Repositories**.*  
> *Universities and national archives contain millions of handwritten manuscripts. But standard SQL databases only support rigid keyword matching, which breaks when historical documents suffer from noisy OCR or archaic spellings. On the other hand, vector databases cannot enforce referential integrity, foreign key cascades, ACID transactions, or access audit trails.*  
> *ArchiveMind solves this by creating a **Hybrid Architecture**: an ACID relational schema managing historical provenance, integrated with a vector similarity engine that matches handwriting stroke embeddings, and full-text search indexing over OCR transcripts."*

---

### **Minute 2: Hybrid Search & Forensic Vector Demonstration**
1. **Show Full-Text Search**:
   * In the search bar on Tab 1, type: `gravitation` or `imitation game`.
   * Click **"Search Archive"**.
   * Point to the result: *"Here we see Newton's Principia or Turing's Imitation Game with high FTS scores."*
2. **Show Handwriting Forensic Vector Matching**:
   * Clear the search box.
   * Under **Handwriting Forensic Reference Vector**, choose: `Leonardo da Vinci (Italian Mirror Script / Left-Handed)`.
   * Click **"Search Archive"**.
   * Point to the scores: *"Notice that even with no text keyword, Da Vinci's Codex Atlanticus and anatomical manuscripts appear at the top with vector cosine similarity > 0.95 because the 128-dimensional stroke contours match."*
3. **Show Hybrid Fusion**:
   * Move the **Alpha Fusion Slider** to `50% SQL / 50% Vec`.
   * Explain the formula:
     $$\text{HybridScore} = \alpha \cdot \text{Score}_{\text{FTS}} + (1 - \alpha) \cdot \text{Similarity}_{\text{Cosine}}$$
   * *"This allows researchers to find documents that match both textual meaning and the handwriting style of a specific scribe."*

---

### **Minute 3: Manuscript Inspector, Checksums & Stored Procedures**
1. Click the **"Inspect"** button on any document (e.g., *Principia Mathematica*).
2. Point out:
   * **Cryptographic Checksum (SHA-256)**: *"Every digitized manuscript is hashed at ingestion to guarantee digital preservation integrity."*
   * **Decoded OCR Transcript**: Cached and synchronized with our FTS virtual table.
3. **Demonstrate Stored Procedure**:
   * Click the button **"+ Chicago Citation"** or **"+ MLA Citation"**.
   * Watch the newly generated citation appear dynamically:
     > *"Sir Isaac Newton, Philosophiae Naturalis Principia Mathematica - Draft Folio 12 (1687), Newtonian Scientific Manuscripts, Cambridge Digital Archives."*
   * Explain: *"This triggers our stored procedure `sp_generate_archival_citation` which executes a multi-table join across `document`, `collection`, `archive`, and `person`, formats the academic citation, and commits it into the `CITATION` table."*

---

### **Minute 4: Provenance Graph & Raspberry Pi Ingestion Station**
1. **Switch to Tab 3: "Provenance Graph"**:
   * Select *Codex Atlanticus* or *Principia*.
   * Explain the canvas graph: *"This visualizes the complete provenance chain: Author (Purple) $\rightarrow$ Manuscript (Amber) $\rightarrow$ Collection (Green) $\rightarrow$ Institution/Archive (Violet) $\rightarrow$ Audited Access Events (Cyan)."*
2. **Switch to Tab 4: "Pi 3B+ Ingestion"**:
   * Explain: *"This simulates our edge scanner. When the Raspberry Pi captures an image, our pipeline crops, deskews, calculates the SHA-256 checksum, extracts handwriting moments, and commits the record within an atomic SQL transaction."*
   * Click **"Process & Ingest"** to show a live successful transaction with generated document ID and checksum!

---

### **Minute 5: The 5 Mandatory DBMS Evaluation Queries (Tab 5)**
Click **Tab 5: "DBMS Evaluation Queries"**. This is the most crucial part for your lab marks!

Show each query by clicking its button:
1. **7.1 Simple Query with GROUP BY & Aggregate**:
   * Point to the output table: Shows count of manuscripts and average OCR character length grouped by `era` and `physical_condition`.
2. **7.2 UPDATE Operation**:
   * Shows updating manuscripts under `'Critical-Decay'` condition to `'Good'` and marking OCR status to `'COMPLETED'`.
3. **7.3 DELETE Operation**:
   * Demonstrates safe deletion of diagnostic entries while foreign keys protect master archive records.
4. **7.4 Correlated Subquery**:
   * Explain: *"This query finds manuscripts whose OCR character length exceeds the average length of documents within their OWN collection. The inner query relies on `d2.collection_id = d1.collection_id`, executing once for each candidate row."*
5. **7.5 Nested Subquery**:
   * Explain: *"This 3-level nested query finds historical authors whose works reside in institutions that curate two or more distinct collections using `HAVING COUNT(col.collection_id) >= 2`."*

Finally, open **Tab 6: "Audit & Triggers"** to show the live rows in `DOCUMENT_VIEW` that were created automatically while you were browsing!

---

## 🧠 3. Top 10 Viva Questions & Winning Answers

### Q1: Why did you choose a Hybrid SQL-Vector approach instead of just using MongoDB or Pinecone?
**Answer**:
> *"Archival management has two conflicting requirements. First, it requires strict ACID transactions, referential integrity (e.g., deleting a collection must cascade or protect documents), role-based permissions, and legal audit trails—which relational databases excel at. Second, it requires semantic and visual handwriting matching across noisy historical scripts—which vector embeddings excel at. By embedding vector cosine search directly alongside relational tables and FTS, ArchiveMind gets the best of both worlds with zero integrity loss."*

### Q2: What is the purpose of the `DOCUMENT_AUTHOR` table? Why is it separate?
**Answer**:
> *"The relationship between `DOCUMENT` and `PERSON` is Many-to-Many ($M:N$). A historical manuscript can have multiple contributors (e.g., an author, a scribe, a signatory), and a person can author multiple manuscripts. `DOCUMENT_AUTHOR` is an associative entity with a composite primary key `(document_id, person_id)` that also stores relationship attributes like `attribution_type` and `confidence_score`."*

### Q3: What is the difference between a Correlated Subquery and a Nested Subquery in your project?
**Answer**:
> *"In a **Nested (Uncorrelated) Subquery** (our Query 7.5), the inner query runs independently once and passes its result set (e.g., archive IDs with $\ge 2$ collections) to the outer query.  
> In a **Correlated Subquery** (our Query 7.4), the inner query references an attribute from the outer query (`d2.collection_id = d1.collection_id`). It must be evaluated repeatedly for every single row examined by the outer query to compute that specific collection's average length."*

### Q4: How do your triggers enforce database integrity?
**Answer**:
> *"We implement two key triggers:  
> 1. `trg_validate_doc_checksum`: Before any document update, it verifies that the SHA-256 cryptographic hash has not been truncated or corrupted, preventing unauthorized payload tampering.  
> 2. `trg_document_tsv_update`: Whenever a document title or OCR text is inserted or modified, the trigger automatically computes and updates the weighted full-text search vector."*

### Q5: What Normal Form is your database in?
**Answer**:
> *"Our relational schema is in **Third Normal Form (3NF)** (and BCNF). Every relation is in 1NF (all attributes are atomic). Every non-key attribute is fully functionally dependent on the entire primary key (satisfying 2NF with no partial dependencies in composite keys). Furthermore, there are no transitive dependencies (satisfying 3NF): non-key attributes depend strictly on the primary key, not on other non-key attributes."*

### Q6: What does the Alpha ($\alpha$) slider do in your search?
**Answer**:
> *"The $\alpha$ parameter controls Reciprocal Rank Fusion (RRF). When $\alpha = 1.0$, the query is 100% keyword BM25 Full-Text Search. When $\alpha = 0.0$, it is 100% handwriting visual cosine similarity. When $\alpha = 0.5$, it calculates a weighted average, ranking documents that balance text relevance with handwriting stroke similarity."*

### Q7: What are the primary and foreign keys of `ACCESS_PERMISSION`?
**Answer**:
> *"The primary key is `permission_id`. It has two foreign keys: `user_id` referencing `APP_USER(user_id)` and `collection_id` referencing `COLLECTION(collection_id)`. We also enforce a `UNIQUE(user_id, collection_id)` constraint so duplicate permission rows cannot exist for the same user and collection."*

### Q8: What happens if an Archive is deleted?
**Answer**:
> *"Due to `ON DELETE CASCADE` on `COLLECTION(archive_id)`, deleting an archive cascades and automatically deletes its child collections, which in turn cascades to delete their associated documents, maintaining strict referential integrity."*

### Q9: How does the Raspberry Pi edge workflow communicate with the DBMS?
**Answer**:
> *"The Raspberry Pi camera captures the physical document, OpenCV performs contour deskewing, and the edge script transmits the preprocessed image and extracted metadata to the FastAPI backend. The server wraps the checksum verification, vector extraction, and relational insertion into an atomic transaction (`BEGIN ... COMMIT`)."*

### Q10: How is chain of custody guaranteed?
**Answer**:
> *"Every time an archivist or researcher inspects a document, a trigger/event writes to the immutable `DOCUMENT_VIEW` table capturing the exact timestamp, the operator's `user_id`, and their client IP address. This tamper-evident log cannot be modified by standard users."*

---

## 📋 4. Checklist for Submission Day
- [x] Database schema defined in PostgreSQL standard DDL (`database/schema_postgres.sql`)
- [x] Sample archival dataset seeded (`database/dml_seed.sql`)
- [x] Stored procedures, functions, and triggers defined (`database/procedures_triggers.sql`)
- [x] Evaluation queries 7.1 to 7.5 tested and working (`database/queries.sql`)
- [x] Full interactive web demo running on FastAPI (`frontend/index.html`)
- [x] Full academic report matching PES University template (`docs/ArchiveMind_DBMS_Project_Report.md`)
- [x] Formatted printable HTML report (`docs/ArchiveMind_DBMS_Project_Report.html`)
- [x] One-click run script (`scripts/run_demo.sh`)

