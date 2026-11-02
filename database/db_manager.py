"""
ArchiveMind Database Manager
Course: UE23CS351A - DBMS Project | PES University
Handles Relational Tables, FTS5 Full-Text Search, Vector Cosine Similarity Engine,
Hybrid Ranking, Stored Procedures, and Chain-of-Custody Triggers.
"""

import sqlite3
import json
import math
import hashlib
import os
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "archivemind.db")

# Deterministic vector generator for handwriting forensics simulation
def generate_deterministic_embedding(seed_str: str, dim: int = 128) -> List[float]:
    rnd = random.Random(seed_str)
    vec = [rnd.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec))
    return [round(x / norm, 6) for x in vec]

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


class ArchiveMindDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_database(self):
        """Initializes tables, FTS index, and loads initial seed data."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self.get_connection()
        cur = conn.cursor()

        # DDL Statements
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS role (
            role_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS app_user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL REFERENCES role(role_id) ON DELETE RESTRICT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS archive (
            archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            institution TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS collection (
            collection_id INTEGER PRIMARY KEY AUTOINCREMENT,
            archive_id INTEGER NOT NULL REFERENCES archive(archive_id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            era TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS access_permission (
            permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
            collection_id INTEGER NOT NULL REFERENCES collection(collection_id) ON DELETE CASCADE,
            permission_type TEXT NOT NULL CHECK (permission_type IN ('READ', 'WRITE', 'ADMIN')),
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, collection_id)
        );

        CREATE TABLE IF NOT EXISTS document (
            document_id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_id INTEGER NOT NULL REFERENCES collection(collection_id) ON DELETE CASCADE,
            digitized_by INTEGER REFERENCES app_user(user_id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            doc_type TEXT NOT NULL,
            date_written TEXT,
            ocr_text_cache TEXT,
            checksum_value TEXT NOT NULL,
            checksum_algorithm TEXT DEFAULT 'SHA-256',
            physical_condition TEXT CHECK (physical_condition IN ('Pristine', 'Good', 'Fragile', 'Critical-Decay')),
            language TEXT DEFAULT 'English',
            image_path TEXT NOT NULL,
            ocr_status TEXT DEFAULT 'COMPLETED',
            digitized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS person (
            person_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            birth_year INTEGER,
            death_year INTEGER,
            biography TEXT
        );

        CREATE TABLE IF NOT EXISTS document_author (
            document_id INTEGER NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
            person_id INTEGER NOT NULL REFERENCES person(person_id) ON DELETE RESTRICT,
            attribution_type TEXT DEFAULT 'Author',
            confidence_score REAL DEFAULT 1.00,
            PRIMARY KEY (document_id, person_id)
        );

        CREATE TABLE IF NOT EXISTS handwriting_sample (
            sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
            vector_id TEXT NOT NULL,
            embedding_json TEXT NOT NULL, -- Stored dense 128-d vector
            extraction_method TEXT DEFAULT 'ResNet50-Forensic-Extractor',
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS document_view (
            view_id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES app_user(user_id) ON DELETE SET NULL,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS citation (
            citation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
            citation_text TEXT NOT NULL,
            citation_style TEXT DEFAULT 'Chicago-Archival',
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- FTS5 Full-Text Search Virtual Table
        CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
            document_id UNINDEXED,
            title,
            ocr_text_cache,
            content=''
        );
        """)

        # Trigger for Document View Logging & Checksum Integrity
        cur.executescript("""
        CREATE TRIGGER IF NOT EXISTS trg_validate_doc_checksum
        BEFORE UPDATE OF checksum_value ON document
        BEGIN
            SELECT CASE 
                WHEN LENGTH(NEW.checksum_value) < 16 THEN
                    RAISE(ABORT, 'Integrity Error: Cryptographic checksum is invalid or truncated.')
            END;
        END;
        """)

        conn.commit()

        # Seed data if empty
        cur.execute("SELECT COUNT(*) FROM role")
        if cur.fetchone()[0] == 0:
            self._seed_data(conn)

        conn.close()

    def _seed_data(self, conn: sqlite3.Connection):
        cur = conn.cursor()
        
        # 1. Roles
        roles = [
            (1, 'Head Archivist'),
            (2, 'Researcher'),
            (3, 'Digitization Tech'),
            (4, 'Auditor')
        ]
        cur.executemany("INSERT INTO role (role_id, role_name) VALUES (?, ?)", roles)

        # 2. Users
        users = [
            (1, 1, 'demo_teacher', 'hash_teacher_admin', 'Demo Teacher', 'demo.teacher@pes.edu'),
            (2, 2, 'sheiman_j', 'hash_sheiman_res', 'A Sheiman Joshi', 'sheiman.pes2ug24cs003@pes.edu'),
            (3, 2, 'abhiroop_r', 'hash_abhiroop_res', 'Abhiroop', 'abhiroop.pes2ug24cs024@pes.edu'),
            (4, 3, 'pi_station_tech', 'hash_scanner_pi', 'Raspberry Pi Station Tech', 'scanner.pi@pes.edu'),
            (5, 4, 'auditor_compliance', 'hash_auditor_sec', 'Archive Compliance Officer', 'audit@pes.edu')
        ]
        cur.executemany("INSERT INTO app_user (user_id, role_id, username, password_hash, full_name, email) VALUES (?, ?, ?, ?, ?, ?)", users)

        # 3. Archives
        archives = [
            (1, 'Cambridge Digital Archives', 'Cambridge, UK', 'Cambridge University Library'),
            (2, 'Vatican Apostolic Manuscript Repository', 'Vatican City', 'Vatican Apostolic Library'),
            (3, 'National Archives of India Special Collections', 'New Delhi, India', 'National Archives of India'),
            (4, 'Bletchley Park Historical Records', 'Milton Keynes, UK', 'Bletchley Park Trust')
        ]
        cur.executemany("INSERT INTO archive (archive_id, name, location, institution) VALUES (?, ?, ?, ?)", archives)

        # 4. Collections
        collections = [
            (1, 1, 'Newtonian Scientific Manuscripts', 'Enlightenment (1680-1720)', 'Original handwritten treatises, draft proofs, and mathematical notebooks of Sir Isaac Newton.'),
            (2, 2, 'Da Vinci Codex & Anatomy Studies', 'Renaissance (1480-1519)', 'Mirror-handwriting sketch folios exploring mechanics, flight, anatomy, and hydraulic engineering.'),
            (3, 3, 'Ramanujan Lost Notebook & Letter Folios', 'Modern Mathematics (1910-1920)', 'Handwritten notes containing over 600 formulae on mock theta functions, partition theory, and continued fractions.'),
            (4, 4, 'Turing Decryption & Computing Dispatches', 'World War II (1939-1950)', 'Bletchley Park Hut 8 cryptanalysis memos, Bombe blueprints, and original draft papers on artificial intelligence.'),
            (5, 1, 'Victorian Analytical Engine Papers', 'Victorian Era (1840-1860)', 'Notes by Ada Lovelace and Charles Babbage detailing computational algorithms for the Analytical Engine.')
        ]
        cur.executemany("INSERT INTO collection (collection_id, archive_id, name, era, description) VALUES (?, ?, ?, ?, ?)", collections)

        # 5. Persons
        persons = [
            (1, 'Sir Isaac Newton', 1642, 1727, 'English polymath active as a mathematician, physicist, astronomer, and author of Principia Mathematica.'),
            (2, 'Leonardo da Vinci', 1452, 1519, 'Italian polymath of the High Renaissance known for his mirror-written codices, flight studies, and mechanical designs.'),
            (3, 'Srinivasa Ramanujan', 1887, 1920, 'Legendary Indian mathematician who made substantial contributions to mathematical analysis, number theory, infinite series, and continued fractions.'),
            (4, 'Alan Turing', 1912, 1954, 'English mathematician, computer scientist, logician, and codebreaker who broke the Enigma code at Bletchley Park.'),
            (5, 'Ada Lovelace', 1815, 1852, 'English mathematician and writer, chiefly known for her work on Charles Babbages proposed mechanical general-purpose computer, the Analytical Engine.'),
            (6, 'Charles Babbage', 1791, 1871, 'English polymath who originated the concept of a digital programmable computer with his Difference and Analytical Engines.')
        ]
        cur.executemany("INSERT INTO person (person_id, full_name, birth_year, death_year, biography) VALUES (?, ?, ?, ?, ?)", persons)

        # 6. Documents
        docs = [
            (1, 1, 3, 'Philosophiae Naturalis Principia Mathematica - Draft Folio 12', 'Manuscript', '1687',
             'Lex I: Corpus omne perseverare in statu suo quiescendi vel movendi uniformiter in directum. The forces acting upon celestial bodies obey the inverse square law of universal gravitation. Calculus fluxions dictate planetary orbital trajectories.',
             'a3f8c149b18361bdfa3490192e21bbd83921048209849208a3821092830192ab', 'Good', 'Latin', 'newton_principia_f12.jpg'),
            
            (2, 1, 3, 'Opticks: On the Dispersion and Refraction of White Light', 'Letter', '1704',
             'Experimentum Crucis: The rays of light passing through triangular prism separate into individual immutable prismatic colors. Violet rays suffer greatest refraction while red rays suffer least.',
             'c9b4e58832a0d912839120938491028301928301928301928301928301928301', 'Fragile', 'English', 'newton_opticks_letter.jpg'),
            
            (3, 2, 3, 'Codex Atlanticus: Folio 104v on Aerial Screws and Vortex Fluid Dynamics', 'Notebook', '1489',
             'La vite aerea: When turned with swiftness, this helical screw made of starched linen will spiral upwards into the air. Water vortices mirror air currents in atmospheric turbulence.',
             '7d3298a4bc102938401928301928301928301928301928301928301928301928', 'Pristine', 'Italian (Mirror-Script)', 'davinci_codex_104v.jpg'),
            
            (4, 2, 3, 'Anatomical Study: Musculature and Tendons of the Human Arm', 'Manuscript', '1510',
             'Observe the balance of antagonistic muscles. The sinews pull in opposing vectors to stabilize the forearm during delicate drawing and tool operation with exact mechanical lever mechanics.',
             '8849bca092102938401928301928301928301928301928301928301928301928', 'Good', 'Italian (Mirror-Script)', 'davinci_anatomy_arm.jpg'),
            
            (5, 3, 3, 'Mock Theta Functions - Final Letter to G.H. Hardy from Madras', 'Letter', '1920-01-12',
             'I am extremely sorry for not writing you a single letter up to now. I have discovered very interesting functions recently which I call Mock Theta functions entering into mathematics as beautifully as ordinary theta functions.',
             'f12089acbd019283019283019283019283019283019283019283019283019283', 'Fragile', 'English', 'ramanujan_letter_hardy.jpg'),
            
            (6, 3, 3, 'Lost Notebook: Modular Equations and Asymptotic Partitions Folio 34', 'Mathematical Treatise', '1919',
             'Formula for partition function p(n) asymptotic series with radical expansions and singular moduli. Integral approximations of extraordinary convergence defying classical analysis.',
             'b55928ca01928301928301928301928301928301928301928301928301928301', 'Critical-Decay', 'English/Tamil', 'ramanujan_lost_notebook_34.jpg'),
            
            (7, 4, 3, 'Hut 8 Cryptanalysis Memo on Enigma Naval 4-Rotor Wirings', 'Letter', '1941-11-04',
             'Banburismus techniques allow reduction of rotor wheel combinations. The Bombe decryption machinery requires synchronized menu configuration for Offizier naval ciphers with indicator sheets.',
             'd449102830192830192830192830192830192830192830192830192830192830', 'Pristine', 'English', 'turing_hut8_memo.jpg'),
            
            (8, 4, 3, 'Computing Machinery and Intelligence: Can Machines Think?', 'Manuscript', '1950',
             'I propose to consider the question, Can machines think? We introduce the imitation game played by an interrogator and two subjects in separate rooms through teletype terminal messages.',
             'e902183019283019283019283019283019283019283019283019283019283019', 'Good', 'English', 'turing_imitation_game.jpg'),
            
            (9, 5, 3, 'Notes on the Analytical Engine: Note G - Bernoulli Number Computation', 'Manuscript', '1843',
             'Note G describes the sequence of operations for calculating Numbers of Bernoulli. The Analytical Engine weaves algebraic patterns just as the Jacquard loom weaves flowers and leaves.',
             '3391028301928301928301928301928301928301928301928301928301928301', 'Good', 'English/French', 'lovelace_note_g_bernoulli.jpg'),
            
            (10, 5, 3, 'Difference Engine Architecture and Logarithmic Tables Proof', 'Mathematical Treatise', '1834',
             'Mechanical calculation via method of finite differences eliminates human transcription error in nautical navigation and astronomical tables via geared brass stepped wheels.',
             '6691028301928301928301928301928301928301928301928301928301928301', 'Fragile', 'English', 'babbage_difference_engine.jpg')
        ]

        for d in docs:
            cur.execute("""
                INSERT INTO document 
                (document_id, collection_id, digitized_by, title, doc_type, date_written, ocr_text_cache, checksum_value, physical_condition, language, image_path, ocr_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED')
            """, d)
            # Insert into FTS
            cur.execute("INSERT INTO document_fts (document_id, title, ocr_text_cache) VALUES (?, ?, ?)", (d[0], d[3], d[6]))

        # 7. Document Authors
        doc_authors = [
            (1, 1, 'Author', 1.00),
            (2, 1, 'Author', 0.98),
            (3, 2, 'Author', 1.00),
            (4, 2, 'Author', 1.00),
            (5, 3, 'Author', 1.00),
            (6, 3, 'Author', 0.95),
            (7, 4, 'Author', 1.00),
            (8, 4, 'Author', 1.00),
            (9, 5, 'Author', 1.00),
            (9, 6, 'Signatory', 0.85),
            (10, 6, 'Author', 1.00)
        ]
        cur.executemany("INSERT INTO document_author (document_id, person_id, attribution_type, confidence_score) VALUES (?, ?, ?, ?)", doc_authors)

        # 8. Handwriting Samples (Forensic dense 128-d vectors clustered per author style)
        style_seeds = {
            1: "newton_quill_flourish",
            2: "newton_quill_flourish",
            3: "davinci_left_mirror_dense",
            4: "davinci_left_mirror_dense",
            5: "ramanujan_fine_nib_slanted",
            6: "ramanujan_fine_nib_slanted",
            7: "turing_fast_slant_draft",
            8: "turing_fast_slant_draft",
            9: "lovelace_copperplate_cursive",
            10: "babbage_geometric_sharp"
        }

        for doc_id, seed in style_seeds.items():
            emb = generate_deterministic_embedding(seed)
            cur.execute("""
                INSERT INTO handwriting_sample (sample_id, document_id, vector_id, embedding_json, extraction_method)
                VALUES (?, ?, ?, ?, 'Pi3B-OpenCV-ContourMoments')
            """, (doc_id, doc_id, f"vec_style_{doc_id}", json.dumps(emb)))

        # 9. Document Views
        views = [
            (1, 1, 2, '192.168.1.105'),
            (2, 1, 1, '192.168.1.10'),
            (3, 3, 2, '192.168.1.105'),
            (4, 5, 2, '192.168.1.105'),
            (5, 7, 1, '192.168.1.10'),
            (6, 9, 2, '192.168.1.105')
        ]
        cur.executemany("INSERT INTO document_view (view_id, document_id, user_id, ip_address) VALUES (?, ?, ?, ?)", views)

        # 10. Citations
        citations = [
            (1, 1, 'Newton, Isaac. Philosophiae Naturalis Principia Mathematica - Draft Folio 12 (1687). Newtonian Scientific Manuscripts, Cambridge Digital Archives.', 'Chicago-Archival'),
            (2, 3, 'Da Vinci, Leonardo. Codex Atlanticus: Folio 104v on Aerial Screws (1489). Da Vinci Codex & Anatomy Studies, Vatican Apostolic Manuscript Repository.', 'Chicago-Archival'),
            (3, 5, 'Ramanujan, Srinivasa. Mock Theta Functions - Final Letter to G.H. Hardy (1920). National Archives of India Special Collections.', 'Chicago-Archival'),
            (4, 7, 'Turing, Alan. Hut 8 Cryptanalysis Memo on Enigma (1941). Bletchley Park Historical Records.', 'Chicago-Archival')
        ]
        cur.executemany("INSERT INTO citation (citation_id, document_id, citation_text, citation_style) VALUES (?, ?, ?, ?)", citations)

        conn.commit()

    # -------------------------------------------------------------
    # HYBRID SEARCH ENGINE (SQL Full-Text + Handwriting Cosine Vector)
    # -------------------------------------------------------------
    def hybrid_search(
        self,
        query_text: str = "",
        sample_vector: Optional[List[float]] = None,
        alpha: float = 0.5, # Weight between text (alpha) and vector (1-alpha)
        collection_id: Optional[int] = None,
        physical_condition: Optional[str] = None,
        author_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cur = conn.cursor()

        # Step 1: Base SQL filter
        where_clauses = ["1=1"]
        params = []
        if collection_id:
            where_clauses.append("d.collection_id = ?")
            params.append(collection_id)
        if physical_condition:
            where_clauses.append("d.physical_condition = ?")
            params.append(physical_condition)
        if author_id:
            where_clauses.append("EXISTS (SELECT 1 FROM document_author da WHERE da.document_id = d.document_id AND da.person_id = ?)")
            params.append(author_id)

        where_sql = " AND ".join(where_clauses)

        # Step 2: Fetch documents and full-text score
        sql = f"""
            SELECT 
                d.document_id,
                d.title,
                d.doc_type,
                d.date_written,
                d.ocr_text_cache,
                d.physical_condition,
                d.language,
                d.image_path,
                d.checksum_value,
                c.name AS collection_name,
                c.era,
                a.name AS archive_name,
                a.institution,
                GROUP_CONCAT(p.full_name, ', ') AS authors,
                hs.embedding_json
            FROM document d
            JOIN collection c ON d.collection_id = c.collection_id
            JOIN archive a ON c.archive_id = a.archive_id
            LEFT JOIN document_author da ON d.document_id = da.document_id
            LEFT JOIN person p ON da.person_id = p.person_id
            LEFT JOIN handwriting_sample hs ON d.document_id = hs.document_id
            WHERE {where_sql}
            GROUP BY d.document_id
        """
        cur.execute(sql, params)
        rows = cur.fetchall()

        # If query_text is provided, perform FTS matching score
        fts_scores = {}
        if query_text.strip():
            # Clean tokens for FTS
            tokens = [t.replace('"', '').replace("'", "") for t in query_text.strip().split() if t.isalnum()]
            if tokens:
                match_query = " OR ".join(tokens)
                try:
                    cur.execute("""
                        SELECT document_id, rank 
                        FROM document_fts 
                        WHERE document_fts MATCH ? 
                        ORDER BY rank
                    """, (match_query,))
                    # SQLite FTS5 rank is negative (lower = better match), normalize to 0..1
                    fts_results = cur.fetchall()
                    if fts_results:
                        min_rank = min(r['rank'] for r in fts_results)
                        max_rank = max(r['rank'] for r in fts_results)
                        diff = (max_rank - min_rank) if max_rank != min_rank else 1.0
                        for r in fts_results:
                            # Higher is better
                            norm_score = 1.0 - ((r['rank'] - min_rank) / diff) if diff > 0 else 1.0
                            fts_scores[int(r['document_id'])] = norm_score
                except Exception:
                    # Fallback substring matching
                    for row in rows:
                        t = row['title'].lower() + " " + (row['ocr_text_cache'] or '').lower()
                        match_count = sum(1 for tok in tokens if tok.lower() in t)
                        if match_count > 0:
                            fts_scores[row['document_id']] = match_count / len(tokens)

        results = []
        for row in rows:
            doc_id = row['document_id']
            # Text score
            text_score = fts_scores.get(doc_id, 0.0)
            if not query_text.strip():
                text_score = 1.0  # Neutral if no text query specified

            # Vector score (Forensic Handwriting Similarity)
            vec_score = 0.0
            if sample_vector and row['embedding_json']:
                try:
                    doc_vec = json.loads(row['embedding_json'])
                    vec_score = cosine_similarity(sample_vector, doc_vec)
                except Exception:
                    vec_score = 0.0
            else:
                vec_score = 1.0 if not sample_vector else 0.0

            # Combined Hybrid Score
            if query_text.strip() and sample_vector:
                hybrid_score = (alpha * text_score) + ((1.0 - alpha) * vec_score)
            elif query_text.strip():
                hybrid_score = text_score
            elif sample_vector:
                hybrid_score = vec_score
            else:
                hybrid_score = 1.0

            # Filter out zero matches if search constraints were given
            if (query_text.strip() or sample_vector) and hybrid_score <= 0.001:
                continue

            results.append({
                "document_id": doc_id,
                "title": row['title'],
                "doc_type": row['doc_type'],
                "date_written": row['date_written'],
                "ocr_snippet": (row['ocr_text_cache'][:160] + "...") if row['ocr_text_cache'] else "",
                "physical_condition": row['physical_condition'],
                "language": row['language'],
                "image_path": row['image_path'],
                "collection_name": row['collection_name'],
                "era": row['era'],
                "archive_name": row['archive_name'],
                "institution": row['institution'],
                "authors": row['authors'] or "Anonymous/Unknown",
                "fts_score": round(text_score, 4),
                "vector_similarity": round(vec_score, 4),
                "hybrid_score": round(hybrid_score, 4)
            })

        # Rank by hybrid score descending
        results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        conn.close()
        return results[:limit]

    # -------------------------------------------------------------
    # STORED PROCEDURE EMULATION: Generate Archival Citation
    # -------------------------------------------------------------
    def generate_citation(self, document_id: int, style: str = "Chicago-Archival") -> Dict[str, Any]:
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                d.title, d.date_written, c.name AS col_name, a.name AS archive_name,
                GROUP_CONCAT(p.full_name, ', ') AS authors
            FROM document d
            JOIN collection c ON d.collection_id = c.collection_id
            JOIN archive a ON c.archive_id = a.archive_id
            LEFT JOIN document_author da ON d.document_id = da.document_id
            LEFT JOIN person p ON da.person_id = p.person_id
            WHERE d.document_id = ?
            GROUP BY d.document_id
        """, (document_id,))
        row = cur.fetchone()

        if not row:
            conn.close()
            raise ValueError(f"Document {document_id} not found.")

        author_str = row['authors'] or "Unknown Author"
        title = row['title']
        date_w = row['date_written'] or "n.d."
        col_name = row['col_name']
        arch_name = row['archive_name']

        if style == "MLA":
            citation_text = f'{author_str}. "{title}." {date_w}. {col_name}, {arch_name}. ArchiveMind Digitized Repository.'
        elif style == "APA":
            citation_text = f'{author_str} ({date_w}). {title} [Archival Manuscript]. {arch_name}, {col_name}.'
        else: # Chicago-Archival
            citation_text = f'{author_str}, {title} ({date_w}), {col_name}, {arch_name}. Digitized preservation record.'

        # Insert or update
        cur.execute("""
            INSERT INTO citation (document_id, citation_text, citation_style, generated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (document_id, citation_text, style))
        citation_id = cur.lastrowid
        conn.commit()
        conn.close()

        return {
            "citation_id": citation_id,
            "document_id": document_id,
            "citation_text": citation_text,
            "citation_style": style,
            "generated_at": datetime.now().isoformat()
        }

    # -------------------------------------------------------------
    # TRIGGER & VIEW LOGGING: Audit Chain of Custody
    # -------------------------------------------------------------
    def record_document_view(self, document_id: int, user_id: Optional[int], ip_address: str = "127.0.0.1") -> int:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO document_view (document_id, user_id, ip_address, viewed_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (document_id, user_id, ip_address))
        view_id = cur.lastrowid
        conn.commit()
        conn.close()
        return view_id

    # -------------------------------------------------------------
    # INGESTION WORKFLOW (Digital Document Preservation & Vector Indexing)
    # -------------------------------------------------------------
    def ingest_document(
        self,
        title: str,
        collection_id: int,
        doc_type: str,
        date_written: str,
        ocr_text: str,
        author_name: str,
        physical_condition: str = "Good",
        language: str = "English",
        digitized_by: int = 3,
        image_name: str = "scanned_manuscript.jpg",
        style_seed: str = "generic_handwriting_pen"
    ) -> Dict[str, Any]:
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            # Generate cryptographic SHA-256 Checksum of the manuscript payload
            raw_data = f"{title}_{ocr_text}_{date_written}".encode('utf-8')
            checksum = hashlib.sha256(raw_data).hexdigest()

            # Insert Document
            cur.execute("""
                INSERT INTO document 
                (collection_id, digitized_by, title, doc_type, date_written, ocr_text_cache, checksum_value, physical_condition, language, image_path, ocr_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED')
            """, (collection_id, digitized_by, title, doc_type, date_written, ocr_text, checksum, physical_condition, language, image_name))
            doc_id = cur.lastrowid

            # Sync FTS
            cur.execute("INSERT INTO document_fts (document_id, title, ocr_text_cache) VALUES (?, ?, ?)", (doc_id, title, ocr_text))

            # Author handling: find or create person
            cur.execute("SELECT person_id FROM person WHERE full_name LIKE ?", (f"%{author_name.strip()}%",))
            p_row = cur.fetchone()
            if p_row:
                person_id = p_row['person_id']
            else:
                cur.execute("INSERT INTO person (full_name, biography) VALUES (?, ?)", (author_name, f"Historical author/contributor of {title}"))
                person_id = cur.lastrowid

            # Link Document Author
            cur.execute("""
                INSERT INTO document_author (document_id, person_id, attribution_type, confidence_score)
                VALUES (?, ?, 'Author', 0.95)
            """, (doc_id, person_id))

            # Generate Forensic Handwriting Embedding Vector
            emb = generate_deterministic_embedding(style_seed or title)
            cur.execute("""
                INSERT INTO handwriting_sample (document_id, vector_id, embedding_json, extraction_method)
                VALUES (?, ?, ?, 'Archival-ForensicMoments')
            """, (doc_id, f"vec_ingest_{doc_id}", json.dumps(emb)))

            # Auto-generate initial Citation
            cur.execute("""
                INSERT INTO citation (document_id, citation_text, citation_style)
                VALUES (?, ?, 'Chicago-Archival')
            """, (doc_id, f"{author_name}, {title} ({date_written}), ArchiveMind Preservation Record."))

            conn.commit()
            return {
                "success": True,
                "document_id": doc_id,
                "checksum": checksum,
                "vector_id": f"vec_ingest_{doc_id}",
                "message": f"Successfully ingested and indexed manuscript '{title}'."
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # -------------------------------------------------------------
    # DBMS EVALUATION QUERIES EXECUTOR
    # -------------------------------------------------------------
    def run_evaluation_query(self, query_key: str) -> Dict[str, Any]:
        conn = self.get_connection()
        cur = conn.cursor()

        queries = {
            "7.1": {
                "name": "7.1 Simple Query with GROUP BY & AGGREGATE",
                "desc": "Aggregate manuscripts across archival eras and physical conditions, computing total counts and average OCR text length.",
                "sql": """
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
                """
            },
            "7.2": {
                "name": "7.2 UPDATE Operation",
                "desc": "Updates conservation condition and verifies checksum integrity for documents under active restoration.",
                "sql": """
                    UPDATE document
                    SET physical_condition = 'Good',
                        ocr_status = 'COMPLETED'
                    WHERE physical_condition = 'Critical-Decay';
                """,
                "is_mutation": True,
                "verify_sql": "SELECT document_id, title, physical_condition, ocr_status FROM document WHERE physical_condition = 'Good' LIMIT 5;"
            },
            "7.3": {
                "name": "7.3 DELETE Operation",
                "desc": "Removes temporary diagnostic view records without compromising permanent archival records.",
                "sql": """
                    DELETE FROM document_view
                    WHERE ip_address LIKE '%[TEMP]%' OR view_id > 1000;
                """,
                "is_mutation": True,
                "verify_sql": "SELECT COUNT(*) AS remaining_audit_records FROM document_view;"
            },
            "7.4": {
                "name": "7.4 Correlated Subquery",
                "desc": "Finds manuscripts whose OCR text length strictly exceeds the average OCR text length of documents within their OWN collection.",
                "sql": """
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
                """
            },
            "7.5": {
                "name": "7.5 Nested Subquery",
                "desc": "Identifies historical authors whose works reside in institutions curating multiple specialized archival collections.",
                "sql": """
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
                """
            }
        }

        q_info = queries.get(query_key)
        if not q_info:
            conn.close()
            raise ValueError(f"Unknown query key: {query_key}. Available: {list(queries.keys())}")

        is_mutation = q_info.get("is_mutation", False)
        sql = q_info["sql"]

        try:
            if is_mutation:
                cur.execute(sql)
                rows_affected = cur.rowcount
                conn.commit()
                # Run verification query
                verify_sql = q_info.get("verify_sql", "SELECT 1;")
                cur.execute(verify_sql)
                rows = [dict(r) for r in cur.fetchall()]
                conn.close()
                return {
                    "key": query_key,
                    "name": q_info["name"],
                    "desc": q_info["desc"],
                    "sql": sql.strip(),
                    "rows_affected": rows_affected,
                    "results": rows
                }
            else:
                cur.execute(sql)
                rows = [dict(r) for r in cur.fetchall()]
                conn.close()
                return {
                    "key": query_key,
                    "name": q_info["name"],
                    "desc": q_info["desc"],
                    "sql": sql.strip(),
                    "results": rows,
                    "count": len(rows)
                }
        except Exception as e:
            conn.close()
            raise e

    # -------------------------------------------------------------
    # PROVENANCE GRAPH DATA EXTRACTOR
    # -------------------------------------------------------------
    def get_provenance_graph(self, document_id: int) -> Dict[str, Any]:
        conn = self.get_connection()
        cur = conn.cursor()

        # Fetch doc info
        cur.execute("""
            SELECT 
                d.document_id, d.title, d.doc_type, d.date_written, d.physical_condition,
                c.collection_id, c.name AS collection_name, c.era,
                a.archive_id, a.name AS archive_name, a.institution, a.location
            FROM document d
            JOIN collection c ON d.collection_id = c.collection_id
            JOIN archive a ON c.archive_id = a.archive_id
            WHERE d.document_id = ?
        """, (document_id,))
        doc = cur.fetchone()
        if not doc:
            conn.close()
            return {"nodes": [], "edges": []}

        # Fetch authors
        cur.execute("""
            SELECT p.person_id, p.full_name, p.birth_year, p.death_year, da.attribution_type, da.confidence_score
            FROM document_author da
            JOIN person p ON da.person_id = p.person_id
            WHERE da.document_id = ?
        """, (document_id,))
        authors = cur.fetchall()

        # Fetch views
        cur.execute("""
            SELECT dv.view_id, dv.viewed_at, dv.ip_address, u.username, u.full_name, r.role_name
            FROM document_view dv
            LEFT JOIN app_user u ON dv.user_id = u.user_id
            LEFT JOIN role r ON u.role_id = r.role_id
            WHERE dv.document_id = ?
            ORDER BY dv.viewed_at DESC LIMIT 5
        """, (document_id,))
        views = cur.fetchall()

        conn.close()

        nodes = []
        edges = []

        # Document node
        doc_node_id = f"doc_{doc['document_id']}"
        nodes.append({
            "id": doc_node_id,
            "label": doc['title'],
            "type": "document",
            "details": f"{doc['doc_type']} ({doc['date_written']})"
        })

        # Collection node
        col_node_id = f"col_{doc['collection_id']}"
        nodes.append({
            "id": col_node_id,
            "label": doc['collection_name'],
            "type": "collection",
            "details": doc['era']
        })
        edges.append({"source": doc_node_id, "target": col_node_id, "label": "BELONGS_TO"})

        # Archive node
        arch_node_id = f"arch_{doc['archive_id']}"
        nodes.append({
            "id": arch_node_id,
            "label": doc['archive_name'],
            "type": "archive",
            "details": f"{doc['institution']} ({doc['location']})"
        })
        edges.append({"source": col_node_id, "target": arch_node_id, "label": "LOCATED_IN"})

        # Author nodes
        for a in authors:
            p_node_id = f"person_{a['person_id']}"
            nodes.append({
                "id": p_node_id,
                "label": a['full_name'],
                "type": "person",
                "details": f"Lifespan: {a['birth_year']}-{a['death_year']}"
            })
            edges.append({
                "source": p_node_id,
                "target": doc_node_id,
                "label": f"{a['attribution_type']} ({int(a['confidence_score']*100)}%)"
            })

        # Audit view nodes
        for v in views:
            v_node_id = f"view_{v['view_id']}"
            nodes.append({
                "id": v_node_id,
                "label": f"View: {v['username'] or 'Guest'}",
                "type": "audit",
                "details": f"{v['viewed_at']} ({v['ip_address']})"
            })
            edges.append({"source": v_node_id, "target": doc_node_id, "label": "AUDITED_ACCESS"})

        return {"nodes": nodes, "edges": edges}

