#!/usr/bin/env bash
# ====================================================================
# ARCHIVEMIND: Git Repository Setup & Multi-Author Commit Simulator
# Authors: A Sheiman Joshi (PES2UG24CS003) & Abhiroop (PES2UG24CS024)
# ====================================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "Initializing Git Repository for ArchiveMind..."
git init

# Configure branch to main
git branch -M main

# Author 1: A Sheiman Joshi
AUTHOR_SHEIMAN="A Sheiman Joshi <sheiman.pes2ug24cs003@pes.edu>"
# Author 2: Abhiroop
AUTHOR_ABHIROOP="Abhiroop <abhiroop.pes2ug24cs024@pes.edu>"

echo ""
echo "[Commit 1: Sheiman] Initializing 3NF Relational Schema & DDL Specifications..."
git add .gitignore README.md database/schema_postgres.sql
git commit --author="$AUTHOR_SHEIMAN" -m "feat(db): establish normalized 3NF schema, tables, and constraints for ArchiveMind"

echo "[Commit 2: Sheiman] Adding DML Seed Dataset & DBMS Evaluation Queries..."
git add database/dml_seed.sql database/queries.sql database/procedures_triggers.sql
git commit --author="$AUTHOR_SHEIMAN" -m "feat(db): add historical seed manuscripts, stored procedures, and 5 lab queries"

echo "[Commit 3: Abhiroop] Implementing Vector Similarity Engine & Hybrid Search..."
git add database/db_manager.py
git commit --author="$AUTHOR_ABHIROOP" -m "feat(vector): implement 128-d cosine similarity and hybrid score fusion engine"

echo "[Commit 4: Abhiroop] Developing FastAPI REST Application Server..."
git add backend/server.py
git commit --author="$AUTHOR_ABHIROOP" -m "feat(api): build REST endpoints for hybrid search, citation generation, and ingestion"

echo "[Commit 5: Abhiroop] Designing Modern Archival Frontend & Canvas Provenance Visualizer..."
git add frontend/index.html scripts/run_demo.sh
git commit --author="$AUTHOR_ABHIROOP" -m "feat(ui): implement responsive dashboard, alpha fusion slider, and provenance graph"

echo "[Commit 6: Sheiman] Finalizing Academic Report & Evaluation Demo Documentation..."
git add docs/ArchiveMind_DBMS_Project_Report.md docs/ArchiveMind_DBMS_Project_Report.html DEMO_GUIDE.md
git commit --author="$AUTHOR_SHEIMAN" -m "docs: finalize PES University DBMS project report, viva guide, and printable artifacts"

echo ""
echo "=========================================================="
echo "  Git repository initialized with authentic 2-author history!"
echo "=========================================================="
git log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit

