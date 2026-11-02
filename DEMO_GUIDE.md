# ArchiveMind — Viva Presentation & Demonstration Guide
### VDUI Project — Archival Intelligence & Hybrid Search Platform

---

## 1. Executive Summary & 2-Minute Project Pitch

> *"Good morning, Professors. ArchiveMind is an AI-powered hybrid SQL–Vector semantic search and preservation platform designed for historical manuscripts.
> While classical archival databases rely strictly on keyword matching—which fails when researchers use modern synonyms or when historical spelling varies—modern vector databases lack relational integrity, ACID transactions, and chain-of-custody triggers.
> ArchiveMind unites both worlds. Using a distributed Edge-AI architecture, a headless Raspberry Pi 3B+ with a 5MP camera acts as the physical manuscript acquisition unit over direct Ethernet, while an NVIDIA RTX 2050 laptop acts as the central AI processing engine.
> When a manuscript is captured, our system validates its SHA-256 cryptographic hash, applies OpenCV bilateral filtering and CLAHE deskewing, transcribes printed or cursive handwriting via PaddleOCR and TrOCR, classifies preservation damage via MobileNetV3, generates real 384-dimensional dense semantic embeddings using sentence-transformers all-MiniLM-L6-v2, and enables hybrid retrieval through weighted $\alpha$ score fusion and Reciprocal Rank Fusion (RRF). Finally, our local RAG assistant answers scholarly questions grounded strictly in primary sources with verifiable citations."*

---

## 2. Live Demonstration Workflow (Step-by-Step)

### Step 1: System Telemetry & Edge Pi Status
- **Tab**: `Overview & Telemetry`
- **What to show**:
  1. Live telemetry card showing Raspberry Pi 3B+ online at **`10.42.0.116`** over Ethernet bus `eno1`.
  2. Point out the **`archivemind-camera.service`** systemd daemon running on the Pi. It starts automatically on boot without needing any monitor or keyboard.
  3. Point out the active **NVIDIA GeForce RTX 2050 (4 GB VRAM)** GPU compute engine and model registry table.

### Step 2: Live Manuscript Acquisition from Raspberry Pi
- **Tab**: `Live Pi Scanner`
- **What to show**:
  1. Place manuscript folio under the Pi Camera module.
  2. Click **`Capture from Pi Camera`**.
  3. The laptop issues `POST http://10.42.0.116:8082/capture`.
  4. The camera shutter triggers via `rpicam-still -n`, verifies JPEG integrity, computes SHA-256 hash, and transfers the payload back to `http://10.42.0.1:8000/api/ingestion/upload`.
  5. The dashboard instantly renders the captured image alongside its cryptographic checksum.

### Step 3: Computer Vision Enhancement & OCR Line Segmentation
- **What to show**:
  1. Show how **Bilateral Denoising** removes parchment fiber noise while preserving crisp iron-gall ink edges.
  2. Explain **CLAHE** (Contrast Limited Adaptive Histogram Equalization) and **Contour Deskewing** ($\pm 25^\circ$).
  3. Toggle recognition mode: *Auto-Detect*, *Handwritten (TrOCR)*, or *Printed (PaddleOCR)*.
  4. Click **`Enhance, OCR & Index into Database`**. The background worker commits the relational records, generates overlapping 80-word chunks, computes real MiniLM embeddings, and indexes into SQLite FTS5.

### Step 4: Hybrid SQL + Vector Semantic Search
- **Tab**: `Hybrid Search`
- **What to show**:
  1. Search for a semantic concept using words that do *not* appear verbatim in the document:  
     **Query**: `"gravitation orbital trajectory"` or `"how machines think imitation"`
  2. Show that at **$\alpha = 1.0$ (Pure SQL FTS5)**, documents without the exact keyword match score zero.
  3. Drag the slider to **$\alpha = 0.0$ (Pure Semantic MiniLM)**: Newton's *Principia Mathematica* or Turing's *Computing Machinery and Intelligence* ranks #1 based purely on vector cosine similarity.
  4. Set **$\alpha = 0.5$ (Balanced Hybrid)**: Demonstrates weighted score fusion and **Reciprocal Rank Fusion (RRF)**.
  5. Highlight the exact matching passage excerpt and score breakdown (`SQL FTS`, `MiniLM VEC`, `HYBRID`).

### Step 5: Local AI Research Assistant (Grounded RAG)
- **Tab**: `AI Research Assistant`
- **What to show**:
  1. Click one of the prompt chips:  
     *"What are the mock theta functions described in Ramanujan's final letter to Hardy?"*
  2. Show how the assistant retrieves primary manuscript chunks, synthesizes a grounded answer, and attaches clickable citation badges: `[Doc #5: Mock Theta Functions Letter (Ramanujan, 1920)]`.
  3. Show the **Hallucination Guardrail**: Ask an irrelevant modern question (*"quantum computing in 2026"*). The assistant refuses to speculate, responding that the primary repository lacks verified evidence.

### Step 6: Manuscript Inspector, Editable OCR & Citation Trigger
- **Tab**: `Inspector & Citation`
- **What to show**:
  1. View the high-resolution folio image, physical condition tag (*Good*, *Stained*, *Fragile*, *Critical-Decay*), and 64-character SHA-256 hash.
  2. Demonstrate **Editable OCR**: Modify a word in the transcription box and click *"Save Correction & Regenerate MiniLM Embeddings"*. Explain that this updates relational cache, refreshes FTS5 virtual table, and replaces outdated vector blobs.
  3. Generate citation in **Chicago-Archival**, **MLA**, or **APA**. Show that this triggers `trg_audit_citation_generation` in the database.

### Step 7: Provenance Graph Topology
- **Tab**: `Provenance Topology`
- **What to show**:
  1. Select a document (e.g. Doc 1: Principia Mathematica).
  2. Show the multi-hop topological graph connecting:  
     $\text{Sir Isaac Newton (Author)} \longrightarrow \text{Principia (Document)} \longrightarrow \text{Newtonian Manuscripts (Collection)} \longrightarrow \text{Cambridge University (Archive)}$.

### Step 8: DBMS Academic Evaluation & Role-Based Access Control (RBAC)
- **Tab**: `DBMS Evaluation`
- **What to show**:
  1. Run **Query 7.1** (Aggregation with `GROUP BY` across eras and physical conditions).
  2. Attempt **Query 7.2** (UPDATE mutation) while logged in as **Abhiroop (Researcher)**:  
     The system blocks execution with:  
     `HTTP 403: RBAC Permission Denied: Modifying relational records requires 'Head Archivist' privileges.`
  3. Switch role dropdown to **Demo Teacher (Head Archivist)**:  
     Re-run Query 7.2 & 7.3: The mutation executes successfully with rollback/verification checks.
  4. Run **Query 7.4** (Correlated Subquery comparing document OCR length against collection average).
  5. Run **Query 7.5** (Nested Subquery with `HAVING COUNT(col.collection_id) >= 2`).

### Step 9: Audit Trail & Triggers
- **Tab**: `Audit & Triggers`
- **What to show**:
  1. Show real-time view logs containing trigger entries like `127.0.0.1 [TRIGGER:CITATION_CHICAGO-ARCHIVAL]`.
  2. Explain how this maintains an unalterable chain-of-custody log.

---

## 3. High-Frequency Viva Questions & Model Answers

### Q1: Why combine SQL Keyword Search and Vector Semantic Search instead of using only one?
**Answer**:
- Keyword search (FTS5 BM25) excels at exact matches: catalog numbers, proper nouns, Latin terminology (e.g. *"Experimentum Crucis"*), and exact dates. However, it fails completely on semantic synonyms or OCR transcription errors.
- Vector search (`all-MiniLM-L6-v2`) understands semantic concepts (e.g. *"celestial orbital gravity"* matches *"forces acting upon celestial bodies"*), but can sometimes retrieve broadly related documents while missing precise historical identifiers.
- Hybrid fusion captures the precision of SQL with the semantic recall of neural embeddings.

### Q2: How does $\alpha$ score fusion work mathematically?
**Answer**:
Given a normalized keyword score $S_{\text{FTS5}} \in [0, 1]$ and vector cosine similarity $S_{\text{MiniLM}} \in [0, 1]$, the combined score is:
$$\text{HybridScore} = \alpha \cdot S_{\text{FTS5}} + (1 - \alpha) \cdot S_{\text{MiniLM}}$$
When $\alpha = 1.0$, the engine operates as pure keyword search. When $\alpha = 0.0$, it operates as pure semantic search. When $\alpha = 0.5$, both modalities contribute equally.

### Q3: What is Reciprocal Rank Fusion (RRF)?
**Answer**:
RRF is an unsupervised ranking fusion method that does not rely on score magnitude calibration. Given document rank $r_{\text{FTS5}}(d)$ and $r_{\text{MiniLM}}(d)$ from both sorted result lists, RRF score is:
$$\text{RRF}(d) = \frac{1}{k + r_{\text{FTS5}}(d)} + \frac{1}{k + r_{\text{MiniLM}}(d)}$$
where $k = 60$ is the standard smoothing constant preventing extreme outlier bias.

### Q4: Why is sentence-transformers/all-MiniLM-L6-v2 used instead of deterministic random vectors?
**Answer**:
Earlier mock systems simulated embeddings using random Gaussian vectors with deterministic seeds. `all-MiniLM-L6-v2` is a real pretrained transformer trained on over 1 billion sentence pairs. It maps semantic meaning into a 384-dimensional hypersphere where semantically similar phrases have high cosine similarity regardless of exact vocabulary.

### Q5: How is the Raspberry Pi 3B+ integrated without overwhelming its 1GB RAM?
**Answer**:
We implemented an **Edge-Capture / Host-Inference** architecture:
- The Pi 3B+ handles only hardware camera capture (`rpicam-still -n`), checksum computation, and HTTP streaming. Heavy neural networks are never loaded on the Pi.
- All heavy AI workloads (CLAHE, TrOCR, MiniLM, MobileNetV3) run on the laptop's AMD Ryzen 5 CPU and NVIDIA RTX 2050 GPU.

### Q6: How does the Pi automatically run without an external monitor or keyboard?
**Answer**:
We configured a native systemd unit file (`archivemind-camera.service`) on Raspberry Pi OS. It is enabled at multi-user target (`WantedBy=multi-user.target`). On boot, systemd initializes the Python daemon, verifies the camera, acquires the static/shared IP `10.42.0.116` on Ethernet, and registers with the laptop.

### Q7: Why store embeddings as float32 binary BLOBs in SQLite rather than an external vector database?
**Answer**:
For archival collections of thousands of folios, SQLite with float32 BLOB storage and NumPy vector operations provides sub-millisecond cosine similarity while eliminating distributed network latency, reducing operational complexity, and preserving atomic ACID transactions between text, metadata, and vectors.
