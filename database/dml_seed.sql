-- ====================================================================
-- ARCHIVEMIND: DML Statements & Seed Records
-- Course: UE23CS351A - DBMS Project | PES University
-- ====================================================================

-- 1. SEED ROLES
INSERT INTO role (role_id, role_name) VALUES
(1, 'Head Archivist'),
(2, 'Researcher'),
(3, 'Digitization Tech'),
(4, 'Auditor')
ON CONFLICT (role_id) DO NOTHING;

-- 2. SEED APP_USERS
INSERT INTO app_user (user_id, role_id, username, password_hash, full_name, email) VALUES
(1, 1, 'dr_shilpa', 'pbkdf2:sha256:archivist_hash_99', 'Dr. Shilpa S', 'shilpa.s@pes.edu'),
(2, 2, 'sheiman_j', 'pbkdf2:sha256:researcher_hash_01', 'A Sheiman Joshi', 'sheiman.pes2ug24cs003@pes.edu'),
(3, 2, 'abhiroop_r', 'pbkdf2:sha256:researcher_hash_02', 'Abhiroop', 'abhiroop.pes2ug24cs024@pes.edu'),
(4, 3, 'pi_station_tech', 'pbkdf2:sha256:tech_hash_44', 'Raspberry Pi Scanner Tech', 'digitization.tech@pes.edu'),
(5, 4, 'auditor_compliance', 'pbkdf2:sha256:auditor_hash_12', 'Archive Compliance Officer', 'audit@pes.edu')
ON CONFLICT (user_id) DO NOTHING;

-- 3. SEED ARCHIVES
INSERT INTO archive (archive_id, name, location, institution) VALUES
(1, 'Cambridge Digital Archives', 'Cambridge, UK', 'Cambridge University Library'),
(2, 'Vatican Apostolic Manuscript Repository', 'Vatican City', 'Vatican Apostolic Library'),
(3, 'National Archives of India Special Collections', 'New Delhi, India', 'National Archives of India'),
(4, 'Bletchley Park Historical Records', 'Milton Keynes, UK', 'Bletchley Park Trust')
ON CONFLICT (archive_id) DO NOTHING;

-- 4. SEED COLLECTIONS
INSERT INTO collection (collection_id, archive_id, name, era, description) VALUES
(1, 1, 'Newtonian Scientific Manuscripts', 'Enlightenment (1680-1720)', 'Original handwritten treatises, draft proofs, and mathematical notebooks of Sir Isaac Newton.'),
(2, 2, 'Da Vinci Codex & Anatomy Studies', 'Renaissance (1480-1519)', 'Mirror-handwriting sketch folios exploring mechanics, flight, anatomy, and hydraulic engineering.'),
(3, 3, 'Ramanujan Lost Notebook & Letter Folios', 'Modern Mathematics (1910-1920)', 'Handwritten notes containing over 600 formulae on mock theta functions, partition theory, and continued fractions.'),
(4, 4, 'Turing Decryption & Computing Dispatches', 'World War II (1939-1950)', 'Bletchley Park Hut 8 cryptanalysis memos, Bombe blueprints, and original draft papers on artificial intelligence.'),
(5, 1, 'Victorian Analytical Engine Papers', 'Victorian Era (1840-1860)', 'Notes by Ada Lovelace and Charles Babbage detailing computational algorithms for the Analytical Engine.')
ON CONFLICT (collection_id) DO NOTHING;

-- 5. SEED ACCESS_PERMISSIONS
INSERT INTO access_permission (user_id, collection_id, permission_type) VALUES
(1, 1, 'ADMIN'),
(1, 2, 'ADMIN'),
(1, 3, 'ADMIN'),
(1, 4, 'ADMIN'),
(1, 5, 'ADMIN'),
(2, 1, 'READ'),
(2, 2, 'READ'),
(2, 3, 'READ'),
(2, 4, 'READ'),
(2, 5, 'READ'),
(3, 1, 'WRITE'),
(3, 3, 'WRITE')
ON CONFLICT DO NOTHING;

-- 6. SEED PERSONS
INSERT INTO person (person_id, full_name, birth_year, death_year, biography) VALUES
(1, 'Sir Isaac Newton', 1642, 1727, 'English polymath active as a mathematician, physicist, astronomer, and author of Principia Mathematica.'),
(2, 'Leonardo da Vinci', 1452, 1519, 'Italian polymath of the High Renaissance known for his mirror-written codices, flight studies, and mechanical designs.'),
(3, 'Srinivasa Ramanujan', 1887, 1920, 'Legendary Indian mathematician who made substantial contributions to mathematical analysis, number theory, infinite series, and continued fractions.'),
(4, 'Alan Turing', 1912, 1954, 'English mathematician, computer scientist, logician, and codebreaker who broke the Enigma code at Bletchley Park.'),
(5, 'Ada Lovelace', 1815, 1852, 'English mathematician and writer, chiefly known for her work on Charles Babbages proposed mechanical general-purpose computer, the Analytical Engine.'),
(6, 'Charles Babbage', 1791, 1871, 'English polymath who originated the concept of a digital programmable computer with his Difference and Analytical Engines.')
ON CONFLICT (person_id) DO NOTHING;

-- 7. SEED DOCUMENTS
INSERT INTO document (document_id, collection_id, digitized_by, title, doc_type, date_written, ocr_text_cache, checksum_value, physical_condition, language, image_path, ocr_status) VALUES
(1, 1, 3, 'Philosophiae Naturalis Principia Mathematica - Draft Folio 12', 'Manuscript', '1687', 'Lex I: Corpus omne perseverare in statu suo quiescendi vel movendi uniformiter in directum. The forces acting upon celestial bodies obey the inverse square law of universal gravitation.', 'a3f8c149b18361bdfa3490192e21bbd83921048209849208a3821092830192ab', 'Good', 'Latin', 'newton_principia_f12.jpg', 'COMPLETED'),
(2, 1, 3, 'Opticks: On the Dispersion and Refraction of White Light', 'Letter', '1704', 'Experimentum Crucis: The rays of light passing through triangular prism separate into individual immutable prismatic colors. Violet rays suffer greatest refraction.', 'c9b4e58832a0d912839120938491028301928301928301928301928301928301', 'Fragile', 'English', 'newton_opticks_letter.jpg', 'COMPLETED'),
(3, 2, 3, 'Codex Atlanticus: Folio 104v on Aerial Screws and Vortex Fluid Dynamics', 'Notebook', '1489', 'La vite aerea: When turned with swiftness, this helical screw made of starched linen will spiral upwards into the air. Water vortices mirror air currents.', '7d3298a4bc102938401928301928301928301928301928301928301928301928', 'Pristine', 'Italian (Mirror-Script)', 'davinci_codex_104v.jpg', 'COMPLETED'),
(4, 2, 3, 'Anatomical Study: Musculature and Tendons of the Human Arm', 'Manuscript', '1510', 'Observe the balance of antagonistic muscles. The sinews pull in opposing vectors to stabilize the forearm during delicate drawing and tool operation.', '8849bca092102938401928301928301928301928301928301928301928301928', 'Good', 'Italian (Mirror-Script)', 'davinci_anatomy_arm.jpg', 'COMPLETED'),
(5, 3, 3, 'Mock Theta Functions - Final Letter to G.H. Hardy from Madras', 'Letter', '1920-01-12', 'I am extremely sorry for not writing you a single letter up to now. I have discovered very interesting functions recently which I call Mock Theta functions.', 'f12089acbd019283019283019283019283019283019283019283019283019283', 'Fragile', 'English', 'ramanujan_letter_hardy.jpg', 'COMPLETED'),
(6, 3, 3, 'Lost Notebook: Modular Equations and Asymptotic Partitions Folio 34', 'Mathematical Treatise', '1919', 'Formula for partition function p(n) asymptotic series with radical expansions and singular moduli. Integral approximations of extraordinary convergence.', 'b55928ca01928301928301928301928301928301928301928301928301928301', 'Critical-Decay', 'English/Tamil', 'ramanujan_lost_notebook_34.jpg', 'COMPLETED'),
(7, 4, 3, 'Hut 8 Cryptanalysis Memo on Enigma Naval 4-Rotor Wirings', 'Letter', '1941-11-04', 'Banburismus techniques allow reduction of rotor wheel combinations. The Bombe decryption machinery requires synchronized menu configuration for Offizier messages.', 'd449102830192830192830192830192830192830192830192830192830192830', 'Pristine', 'English', 'turing_hut8_memo.jpg', 'COMPLETED'),
(8, 4, 3, 'Computing Machinery and Intelligence: Can Machines Think?', 'Manuscript', '1950', 'I propose to consider the question, Can machines think? We introduce the imitation game played by an interrogator and two subjects in separate rooms.', 'e902183019283019283019283019283019283019283019283019283019283019', 'Good', 'English', 'turing_imitation_game.jpg', 'COMPLETED'),
(9, 5, 3, 'Notes on the Analytical Engine: Note G - Bernoulli Number Computation', 'Manuscript', '1843', 'Note G describes the sequence of operations for calculating Numbers of Bernoulli. The Analytical Engine weaves algebraic patterns just as the Jacquard loom weaves flowers.', '3391028301928301928301928301928301928301928301928301928301928301', 'Good', 'English/French', 'lovelace_note_g_bernoulli.jpg', 'COMPLETED'),
(10, 5, 3, 'Difference Engine Architecture and Logarithmic Tables Proof', 'Mathematical Treatise', '1834', 'Mechanical calculation via method of finite differences eliminates human transcription error in nautical navigation and astronomical tables.', '6691028301928301928301928301928301928301928301928301928301928301', 'Fragile', 'English', 'babbage_difference_engine.jpg', 'COMPLETED')
ON CONFLICT (document_id) DO NOTHING;

-- 8. SEED DOCUMENT_AUTHOR RELATIONSHIPS
INSERT INTO document_author (document_id, person_id, attribution_type, confidence_score) VALUES
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
ON CONFLICT DO NOTHING;

-- 9. SEED HANDWRITING_SAMPLES (Forensic Stroke Feature Vectors)
INSERT INTO handwriting_sample (sample_id, document_id, vector_id, extraction_method) VALUES
(1, 1, 'vec_newton_latin_cursive_01', 'Pi3B-OpenCV-ContourMoments'),
(2, 2, 'vec_newton_ink_quill_02', 'Pi3B-OpenCV-ContourMoments'),
(3, 3, 'vec_davinci_mirror_lh_01', 'Pi3B-OpenCV-ContourMoments'),
(4, 4, 'vec_davinci_hatching_lh_02', 'Pi3B-OpenCV-ContourMoments'),
(5, 5, 'vec_ramanujan_slanted_pen_01', 'Pi3B-OpenCV-ContourMoments'),
(6, 6, 'vec_ramanujan_micro_math_02', 'Pi3B-OpenCV-ContourMoments'),
(7, 7, 'vec_turing_quick_draft_01', 'Pi3B-OpenCV-ContourMoments'),
(8, 8, 'vec_turing_typewritten_margin_02', 'Pi3B-OpenCV-ContourMoments'),
(9, 9, 'vec_lovelace_elegant_copperplate_01', 'Pi3B-OpenCV-ContourMoments'),
(10, 10, 'vec_babbage_geometric_notes_01', 'Pi3B-OpenCV-ContourMoments')
ON CONFLICT (sample_id) DO NOTHING;

-- 10. SEED DOCUMENT_VIEWS (Audit Trail)
INSERT INTO document_view (view_id, document_id, user_id, viewed_at, ip_address) VALUES
(1, 1, 2, CURRENT_TIMESTAMP - INTERVAL '2 days', '192.168.1.105'),
(2, 1, 1, CURRENT_TIMESTAMP - INTERVAL '1 day', '192.168.1.10'),
(3, 3, 2, CURRENT_TIMESTAMP - INTERVAL '12 hours', '192.168.1.105'),
(4, 5, 2, CURRENT_TIMESTAMP - INTERVAL '5 hours', '192.168.1.105'),
(5, 7, 1, CURRENT_TIMESTAMP - INTERVAL '2 hours', '192.168.1.10'),
(6, 9, 2, CURRENT_TIMESTAMP - INTERVAL '30 minutes', '192.168.1.105')
ON CONFLICT (view_id) DO NOTHING;

-- 11. SEED CITATIONS
INSERT INTO citation (citation_id, document_id, citation_text, citation_style) VALUES
(1, 1, 'Newton, Isaac. Philosophiae Naturalis Principia Mathematica - Draft Folio 12 (1687). Newtonian Scientific Manuscripts, Cambridge Digital Archives.', 'Chicago-Archival'),
(2, 3, 'Da Vinci, Leonardo. Codex Atlanticus: Folio 104v on Aerial Screws (1489). Da Vinci Codex & Anatomy Studies, Vatican Apostolic Manuscript Repository.', 'Chicago-Archival'),
(3, 5, 'Ramanujan, Srinivasa. Mock Theta Functions - Final Letter to G.H. Hardy (1920). National Archives of India Special Collections.', 'Chicago-Archival'),
(4, 7, 'Turing, Alan. Hut 8 Cryptanalysis Memo on Enigma (1941). Bletchley Park Historical Records.', 'Chicago-Archival')
ON CONFLICT (citation_id) DO NOTHING;

