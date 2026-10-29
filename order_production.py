"""Headless book production shared by the cloud worker (no browser/session dependency)."""
import json
import logging
import os
import re
import time
from pathlib import Path
from production_status import ProgressTracker

SUPABASE_BUCKET = "my-little-hero-files"
ADMIN_WORK_DIR = Path(os.getenv("MLH_WORK_DIR", "worker_orders"))

def get_supabase_client():
    from supabase import create_client
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_SECRET_KEY", "").strip()
           or os.getenv("SUPABASE_SERVICE_KEY", "").strip())
    if not url or not key:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SECRET_KEY sont requis.")
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
            logging.info(
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


def generate_order(order):
    from book_engine import generate_book_from_adventure
    report = ProgressTracker(order, lambda fields: update_order_fields(order["order_ref"], fields))
    if not order.get("adventures"):
        raise ValueError("Aucune aventure dans cette commande.")
    total = len(order["adventures"])
    report("assets", "Récupération de la référence et des couvertures", book_index=1, book_total=total)
    reference_path, preview_covers = ensure_order_assets(order)

    if len(preview_covers) < len(order["adventures"]):
        raise FileNotFoundError("Une ou plusieurs couvertures sont introuvables.")

    supabase = get_supabase_client()
    final_dir = order["_dir"] / "final_books"
    final_dir.mkdir(parents=True, exist_ok=True)

    generated_files = list(order.get("generated_files") or [])
    total = len(order["adventures"])

    for index, adventure in enumerate(order["adventures"], start=1):
        title = (adventure.get("title") or "").strip()
        if not title:
            raise ValueError(f"Le titre de l'aventure {index} est manquant.")

        logging.info(f"**{index}/{total} — {title}**")

        existing_remote = get_remote_generated_for_index(order, index)

        if existing_remote:
            download_existing_pdf_if_needed(order, index, existing_remote)
            report("upload", f"Livre {index}/{total} déjà enregistré", book_index=index, completed_books=index)
            logging.info(f"⏭️ {index}/{total} déjà terminé — aucune régénération.")
            continue

        adventure_dir = final_dir / f"adventure_{index:02d}"
        adventure_dir.mkdir(parents=True, exist_ok=True)

        expected_pdf = adventure_dir / (
            f"{_safe_filename(order['child_name'])}_"
            f"{_safe_filename(title)}.pdf"
        )

        if expected_pdf.exists() and expected_pdf.stat().st_size > 0:
            report("pdf", f"PDF du livre {index}/{total} conservé — aucune régénération", book_index=index, page_index=10, page_total=10)
            pdf_path = expected_pdf
        else:
            pdf_path = generate_book_from_adventure(
                child_name=order["child_name"],
                age=int(order["age"]),
                theme=adventure["theme"],
                language=order["language"],
                client_idea=adventure.get("idea", ""),
                child_gender=adventure.get("child_gender", ""),
                child_quality=adventure.get("quality", ""),
                book_title=title,
                reference_path=reference_path,
                output_dir=adventure_dir,
                preview_cover_path=preview_covers[index - 1],
                progress=lambda stage, label, **details: report(stage, label, book_index=index, **details),
            )

        pdf_path = Path(pdf_path)

        remote_pdf_path = (
            f"orders/{order['order_ref']}/final_books/"
            f"adventure_{index:02d}/book_{index:02d}.pdf"
        )

        report("upload", f"Envoi du PDF {index}/{total} vers le stockage privé", book_index=index)
        storage_upload(
            supabase,
            remote_pdf_path,
            pdf_path,
            "application/pdf",
        )

        if remote_pdf_path not in generated_files:
            generated_files.append(remote_pdf_path)

        order["generated_files"] = generated_files
        report("upload", f"Livre {index}/{total} enregistré", book_index=index, completed_books=index)

        update_order_fields(
            order["order_ref"],
            {
                "generated_files": generated_files,
                "status": "GENERATING",
            },
        )

        logging.info(f"✅ Livre {index}/{total} enregistré dans Supabase.")

    order["generated_files"] = generated_files

    update_order_fields(
        order["order_ref"],
        {
            "generated_files": generated_files,
            "status": "BOOKS_READY",
        },
    )

    order["status"] = "BOOKS_READY"
    report("complete", "Tous les livres sont prêts à télécharger", completed_books=total)
    return generated_files
