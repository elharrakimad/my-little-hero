import json
import hmac
import os
from datetime import datetime
from pathlib import Path
import re
import time

import streamlit as st
from supabase import create_client


# ============================================================
# MY LITTLE HERO — ADMIN
# Client en ligne -> Supabase DB + Storage -> Admin local
# ============================================================

st.set_page_config(
    page_title="My Little Hero — Admin",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

SUPABASE_BUCKET = "my-little-hero-files"
ADMIN_WORK_DIR = Path("admin_orders")

STATUS_LABELS = {
    "WAITING_FOR_PAYMENT": "⏳ En attente de paiement",
    "PAID": "✅ Paiement vérifié",
    "GENERATING": "⚙️ Génération en cours",
    "GENERATION_INTERRUPTED": "⚠️ Production interrompue",
    "BOOKS_READY": "📕 Livres prêts",
    "SHIPPED": "📦 Expédiée",
    "DELIVERED": "🎉 Livrée",
    "CANCELLED": "❌ Annulée",
}

STATUS_BADGES = {
    "WAITING_FOR_PAYMENT": "🟡",
    "PAID": "🟢",
    "GENERATING": "🔵",
    "GENERATION_INTERRUPTED": "🟠",
    "BOOKS_READY": "🟣",
    "SHIPPED": "📦",
    "DELIVERED": "🎉",
    "CANCELLED": "🔴",
}


# ------------------------------------------------------------
# SUPABASE
# ------------------------------------------------------------

def get_supabase_client():
    url = (
        os.getenv("SUPABASE_URL", "").strip()
        or str(st.secrets.get("SUPABASE_URL", "")).strip()
    )
    key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_KEY", "").strip()
        or str(st.secrets.get("SUPABASE_SECRET_KEY", "")).strip()
        or str(st.secrets.get("SUPABASE_SERVICE_KEY", "")).strip()
    )

    if not url or not key:
        raise RuntimeError(
            "Supabase n'est pas configuré. Ajoute SUPABASE_URL et "
            "SUPABASE_SECRET_KEY dans les variables d'environnement de l'Admin."
        )

    return create_client(url, key)


def _is_transient_network_error(exc):
    text = str(exc).lower()
    return (
        "winerror 10035" in text
        or "operation non bloquante" in text
        or "would block" in text
        or "temporarily unavailable" in text
        or "connection reset" in text
        or "connection aborted" in text
        or "timeout" in text
    )


def _retry_storage(operation, label: str, attempts: int = 6):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            if not _is_transient_network_error(exc) or attempt == attempts:
                raise
            wait = attempt * 2
            st.warning(
                f"🌐 Connexion temporairement indisponible pendant {label}. "
                f"Nouvelle tentative {attempt + 1}/{attempts} dans {wait}s..."
            )
            time.sleep(wait)
    raise last_error


def storage_download(supabase, storage_path: str, local_path: Path):
    local_path.parent.mkdir(parents=True, exist_ok=True)

    data = _retry_storage(
        lambda: supabase.storage.from_(SUPABASE_BUCKET).download(storage_path),
        f"le téléchargement de {Path(storage_path).name}",
    )

    local_path.write_bytes(data)
    return local_path


def storage_upload(supabase, storage_path: str, local_path: Path, content_type: str):
    data = local_path.read_bytes()

    _retry_storage(
        lambda: supabase.storage.from_(SUPABASE_BUCKET).upload(
            storage_path,
            data,
            file_options={"content-type": content_type, "upsert": "true"},
        ),
        f"l'envoi de {Path(storage_path).name}",
    )

    return storage_path


def update_order_fields(order_ref: str, fields: dict):
    def operation():
        supabase = get_supabase_client()
        return (
            supabase.table("orders")
            .update(fields)
            .eq("order_ref", order_ref)
            .execute()
        )

    return _retry_storage(
        operation,
        "la mise à jour de la commande",
        attempts=6,
    )


# ------------------------------------------------------------
# AUTHENTIFICATION ADMIN
# ------------------------------------------------------------

def get_admin_password():
    password = os.getenv("MY_LITTLE_HERO_ADMIN_PASSWORD", "")
    if password:
        return password
    try:
        return str(st.secrets.get("MY_LITTLE_HERO_ADMIN_PASSWORD", ""))
    except Exception:
        return ""


def login():
    if st.session_state.get("admin_authenticated"):
        return True

    st.markdown(
        """
        <div style='text-align:center;padding:55px 10px 20px;'>
            <div style='font-size:48px;'>🔐</div>
            <h1>My Little Hero — Administration</h1>
            <p style='color:#777;'>Espace privé de gestion des commandes</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    configured_password = get_admin_password()
    if not configured_password:
        st.error(
            "Le mot de passe administrateur n'est pas configuré. "
            "Définis MY_LITTLE_HERO_ADMIN_PASSWORD avant de lancer admin.py."
        )
        st.code(
            '$env:MY_LITTLE_HERO_ADMIN_PASSWORD="TonMotDePasseFort"',
            language="powershell",
        )
        st.stop()

    password = st.text_input("Mot de passe administrateur", type="password")
    if st.button("🔓 Se connecter", type="primary", use_container_width=True):
        if hmac.compare_digest(password, configured_password):
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")

    return False


if not login():
    st.stop()


# ------------------------------------------------------------
# OUTILS COMMANDES
# ------------------------------------------------------------

def safe_local_dir(order_ref: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", str(order_ref))
    path = ADMIN_WORK_DIR / safe
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_order(row: dict) -> dict:
    order_ref = row.get("order_ref") or str(row.get("id", ""))
    adventures = row.get("adventures") or []
    cover_paths = row.get("cover_paths") or []
    generated_files = row.get("generated_files") or []

    if isinstance(adventures, str):
        try:
            adventures = json.loads(adventures)
        except Exception:
            adventures = []

    if isinstance(cover_paths, str):
        try:
            cover_paths = json.loads(cover_paths)
        except Exception:
            cover_paths = []

    if isinstance(generated_files, str):
        try:
            generated_files = json.loads(generated_files)
        except Exception:
            generated_files = []

    order = {
        "id": row.get("id"),
        "order_ref": order_ref,
        "order_number": order_ref,
        "preview_id": order_ref,
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "status": row.get("status", "WAITING_FOR_PAYMENT"),
        "child_name": row.get("child_name", ""),
        "customer_phone": row.get("parent_phone", ""),
        "customer_email": row.get("parent_email", ""),
        "age": row.get("child_age", ""),
        "language": row.get("language", ""),
        "pack": row.get("pack", ""),
        "adventure_count": row.get("adventure_count", len(adventures)),
        "format": row.get("format", "—"),
        "price": row.get("total_price", "—"),
        "reference_path": row.get("reference_path", ""),
        "cover_paths": cover_paths,
        "adventures": adventures,
        "generated_files": generated_files,
        "last_error": row.get("last_error"),
        "generation_progress": row.get("generation_progress") or {},
    }
    order["_dir"] = safe_local_dir(order_ref)
    return order


def list_orders():
    supabase = get_supabase_client()
    response = (
        supabase.table("orders")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return [normalize_order(row) for row in (response.data or [])]


def format_date(order):
    value = order.get("created_at")
    if not value:
        return "—"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(value)[:16]


def whatsapp_link(phone):
    digits = re.sub(r"\D", "", str(phone or ""))
    if not digits:
        return None
    if digits.startswith("0"):
        digits = "212" + digits[1:]
    elif digits.startswith("212"):
        pass
    elif len(digits) == 9:
        digits = "212" + digits
    else:
        return None
    return f"https://wa.me/{digits}"


def update_status(order, status):
    now = datetime.now().isoformat(timespec="seconds")
    update_order_fields(
        order["order_ref"],
        {"status": status},
    )
    order["status"] = status
    order["updated_at"] = now


def _safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9À-ÿ _-]", "", str(value)).strip()
    value = re.sub(r"\s+", "_", value)
    return value[:80] or "livre"


def ensure_order_assets(order):
    supabase = get_supabase_client()
    order_dir = order["_dir"]

    reference_remote = order.get("reference_path")
    if not reference_remote:
        raise FileNotFoundError("Référence personnage absente de la commande.")

    reference_local = order_dir / "character_reference.png"
    if not reference_local.exists() or reference_local.stat().st_size == 0:
        storage_download(supabase, reference_remote, reference_local)

    local_covers = []
    for index, remote_path in enumerate(order.get("cover_paths", []), start=1):
        local_cover = order_dir / f"cover_{index:02d}.png"
        if not local_cover.exists() or local_cover.stat().st_size == 0:
            storage_download(supabase, remote_path, local_cover)
        local_covers.append(local_cover)

    return reference_local, local_covers


def get_remote_generated_for_index(order, index):
    marker = f"/adventure_{index:02d}/"
    for remote_path in order.get("generated_files", []):
        if marker in str(remote_path):
            return str(remote_path)
    return None


def download_existing_pdf_if_needed(order, index, remote_path):
    if not remote_path:
        return None

    order_dir = order["_dir"]
    local_dir = order_dir / "final_books" / f"adventure_{index:02d}"
    local_dir.mkdir(parents=True, exist_ok=True)

    local_path = local_dir / Path(remote_path).name
    if local_path.exists() and local_path.stat().st_size > 0:
        return local_path

    supabase = get_supabase_client()
    return storage_download(supabase, remote_path, local_path)





from admin_dashboard import show_dashboard

show_dashboard(list_orders, get_supabase_client, download_existing_pdf_if_needed, update_status)
