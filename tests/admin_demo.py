"""Synthetic local-only dashboard data for UI verification. No production credentials."""
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st
from admin_dashboard import show_dashboard

st.set_page_config(page_title="My Little Hero — Aperçu administration", layout="wide")
now = datetime.now(timezone.utc).isoformat()
base = {"age": 8, "language": "Français", "pack": "LITTLE HERO", "price": 69,
    "adventure_count": 1, "created_at": now, "generated_files": [],
    "adventures": [{"title": "Le secret des étoiles", "theme": "Espace"}]}
orders = [
    {**base, "order_ref": "DEMO-001", "child_name": "Amina", "status": "GENERATING",
     "generation_progress": {"stage": "illustrations", "label": "Illustration 7/10 en cours", "percent": 54,
        "book_index": 1, "book_total": 1, "page_index": 6, "page_total": 10, "updated_at": now,
        "history": [{"at": now, "stage": "story", "message": "Histoire enregistrée"}]}},
    {**base, "order_ref": "DEMO-002", "child_name": "Yassine", "status": "GENERATION_INTERRUPTED",
     "generation_progress": {"stage": "error", "failed_stage": "upload", "percent": 96, "page_index": 10,
        "updated_at": now, "error": "Échec de l'enregistrement du PDF. Le fichier est conservé et prêt à être renvoyé."}},
    {**base, "order_ref": "DEMO-003", "child_name": "Adam", "status": "WAITING_FOR_PAYMENT"},
]
show_dashboard(lambda: orders, lambda: None, lambda *args: None, lambda *args: None)
