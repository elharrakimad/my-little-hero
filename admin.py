import json
import os
from datetime import datetime
from pathlib import Path
import re
import time

import streamlit as st
from supabase import create_client

from book_engine import generate_book_from_adventure

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
        if password == configured_password:
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


def generate_order(order):
    if not order.get("adventures"):
        raise ValueError("Aucune aventure dans cette commande.")

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

        st.write(f"**{index}/{total} — {title}**")

        existing_remote = get_remote_generated_for_index(order, index)

        if existing_remote:
            download_existing_pdf_if_needed(order, index, existing_remote)
            st.info(f"⏭️ {index}/{total} déjà terminé — aucune régénération.")
            continue

        adventure_dir = final_dir / f"adventure_{index:02d}"
        adventure_dir.mkdir(parents=True, exist_ok=True)

        expected_pdf = adventure_dir / (
            f"{_safe_filename(order['child_name'])}_"
            f"{_safe_filename(title)}.pdf"
        )

        if expected_pdf.exists() and expected_pdf.stat().st_size > 0:
            pdf_path = expected_pdf
        else:
            pdf_path = generate_book_from_adventure(
                child_name=order["child_name"],
                age=int(order["age"]),
                theme=adventure["theme"],
                language=order["language"],
                client_idea=adventure.get("idea", ""),
                child_quality=adventure.get("quality", ""),
                book_title=title,
                reference_path=reference_path,
                output_dir=adventure_dir,
                preview_cover_path=preview_covers[index - 1],
            )

        pdf_path = Path(pdf_path)

        remote_pdf_path = (
            f"orders/{order['order_ref']}/final_books/"
            f"adventure_{index:02d}/{pdf_path.name}"
        )

        storage_upload(
            supabase,
            remote_pdf_path,
            pdf_path,
            "application/pdf",
        )

        if remote_pdf_path not in generated_files:
            generated_files.append(remote_pdf_path)

        order["generated_files"] = generated_files

        update_order_fields(
            order["order_ref"],
            {
                "generated_files": generated_files,
                "status": "GENERATING",
            },
        )

        st.success(f"✅ Livre {index}/{total} enregistré dans Supabase.")

    order["generated_files"] = generated_files

    update_order_fields(
        order["order_ref"],
        {
            "generated_files": generated_files,
            "status": "BOOKS_READY",
        },
    )

    order["status"] = "BOOKS_READY"
    return generated_files


# ------------------------------------------------------------
# STYLE
# ------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Poppins:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    h1, h2, h3 { font-family: 'Baloo 2', sans-serif !important; }
    .admin-header {
        background: linear-gradient(135deg,#303047,#6c63ff);
        color: white;
        padding: 22px 28px;
        border-radius: 22px;
        margin-bottom: 22px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# HEADER / SIDEBAR
# ------------------------------------------------------------

st.markdown(
    """
    <div class='admin-header'>
        <div style='font-size:15px;opacity:.85;'>🌟 MY LITTLE HERO</div>
        <div style='font-size:32px;font-weight:800;'>Tableau de bord commandes</div>
        <div style='opacity:.9;'>Vérifier les paiements et lancer la production des livres.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### 🔐 Administration")
    st.caption("Cet espace ne doit pas être partagé avec les clients.")
    if st.button("🔄 Actualiser", use_container_width=True):
        st.rerun()
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.rerun()


# ------------------------------------------------------------
# CHARGEMENT SUPABASE
# ------------------------------------------------------------

try:
    orders = list_orders()
except Exception as exc:
    st.error(f"Impossible de charger les commandes Supabase : {exc}")
    st.stop()


# ------------------------------------------------------------
# FILTRES / STATISTIQUES
# ------------------------------------------------------------

status_filter = st.selectbox(
    "Filtrer les commandes",
    ["Toutes"] + list(STATUS_LABELS.keys()),
    format_func=lambda value: "Toutes" if value == "Toutes" else STATUS_LABELS[value],
)

filtered = (
    orders
    if status_filter == "Toutes"
    else [o for o in orders if o.get("status") == status_filter]
)

counts = {
    status: sum(o.get("status") == status for o in orders)
    for status in STATUS_LABELS
}

a, b, c, d = st.columns(4)
with a:
    st.metric("📦 Total", len(orders))
with b:
    st.metric("⏳ À vérifier", counts["WAITING_FOR_PAYMENT"])
with c:
    st.metric("⚙️ En production", counts["GENERATING"])
with d:
    st.metric("📕 Prêtes", counts["BOOKS_READY"])

st.divider()

if not filtered:
    st.info("Aucune commande dans cette catégorie.")
    st.stop()


# ------------------------------------------------------------
# COMMANDES
# ------------------------------------------------------------

for order in filtered:
    status = order.get("status", "WAITING_FOR_PAYMENT")
    badge = STATUS_BADGES.get(status, "⚪")
    order_ref = order["order_ref"]

    with st.container(border=True):
        top1, top2 = st.columns([3, 1])

        with top1:
            st.markdown(
                f"### {badge} {order.get('child_name', 'Sans nom')} — "
                f"{order.get('pack', '?')}"
            )
            st.caption(
                f"Commande : {order_ref}  •  Créée : {format_date(order)}"
            )

        with top2:
            st.markdown(f"**{STATUS_LABELS.get(status, status)}**")
            st.markdown(f"**{order.get('price', '?')} DH**")

        info1, info2, info3, info4 = st.columns(4)
        with info1:
            st.write(f"👦 **Âge :** {order.get('age', '—')}")
        with info2:
            st.write(f"🌍 **Langue :** {order.get('language', '—')}")
        with info3:
            st.write(f"🎁 **Format :** {order.get('format', '—')}")
        with info4:
            st.write(
                f"📚 **Aventures :** "
                f"{order.get('adventure_count', len(order.get('adventures', [])))}"
            )

        phone = order.get("customer_phone", "")
        email = order.get("customer_email", "")
        wa = whatsapp_link(phone)

        if phone:
            if wa:
                st.markdown(f"📱 **WhatsApp parent :** [{phone}]({wa})")
            else:
                st.write(f"📱 **Téléphone parent :** {phone}")
        else:
            st.caption("📱 Aucun numéro WhatsApp enregistré.")

        if email:
            st.markdown(f"📧 **E-mail parent :** [{email}](mailto:{email})")
        else:
            st.write("📧 **E-mail parent :** —")

        adventures = order.get("adventures", [])
        if adventures:
            st.markdown("**Aventures**")
            for adventure in adventures:
                st.write(
                    f"{adventure.get('number', '')}. "
                    f"**{adventure.get('title', 'Titre manquant')}** — "
                    f"{adventure.get('theme', '')}"
                )

        st.markdown("---")

        if status == "WAITING_FOR_PAYMENT":
            st.warning(
                "💳 Vérifie avec le parent le moyen de paiement convenu "
                "(virement ou paiement à la livraison) avant de confirmer."
            )

            confirm = st.checkbox(
                "☑️ J'ai vérifié le paiement / les conditions de paiement.",
                key=f"confirm_payment_{order_ref}",
            )

            if st.button(
                "✅ Confirmer la commande",
                key=f"paid_{order_ref}",
                type="primary",
                disabled=not confirm,
                use_container_width=True,
            ):
                update_status(order, "PAID")
                st.success("Commande confirmée. La production peut commencer.")
                st.rerun()

        elif status in ("PAID", "GENERATING", "GENERATION_INTERRUPTED"):
            if status == "PAID":
                st.success("💳 Commande confirmée. Tu peux lancer la production.")
            elif status == "GENERATING":
                st.warning(
                    "⚙️ Cette commande était en cours de génération. "
                    "Tu peux reprendre la production."
                )
            else:
                st.warning(
                    "⚠️ La production a été interrompue. "
                    "Les livres déjà terminés ne seront pas régénérés."
                )

            button_label = (
                "🚀 Générer les livres"
                if status == "PAID"
                else "🔄 Reprendre la production"
            )

            if st.button(
                button_label,
                key=f"generate_{order_ref}",
                type="primary",
                use_container_width=True,
            ):
                try:
                    update_status(order, "GENERATING")
                    st.info(
                        "La production est lancée. "
                        "Les livres déjà terminés seront ignorés."
                    )
                    generated = generate_order(order)
                    st.success(f"✅ {len(generated)} livre(s) prêt(s).")
                    st.rerun()

                except Exception as exc:
                    error_text = str(exc)
                    now = datetime.now().isoformat(timespec="seconds")

                    try:
                        update_order_fields(
                            order_ref,
                            {
                                "status": "GENERATION_INTERRUPTED",
                            },
                        )
                    except Exception:
                        # Si Supabase est momentanément indisponible, on conserve
                        # l'erreur principale sans la masquer par une seconde erreur.
                        pass

                    st.error(
                        "❌ La génération a été interrompue. "
                        f"Les livres déjà terminés sont conservés. Détail : {error_text}"
                    )

        elif status == "BOOKS_READY":
            st.success("📕 Les livres sont prêts.")

            generated_files = order.get("generated_files", [])

            for i, remote_path in enumerate(generated_files, start=1):
                try:
                    local_pdf = download_existing_pdf_if_needed(
                        order,
                        i,
                        remote_path,
                    )

                    if local_pdf and local_pdf.exists():
                        st.download_button(
                            f"📥 Télécharger le livre {i}",
                            data=local_pdf.read_bytes(),
                            file_name=local_pdf.name,
                            mime="application/pdf",
                            key=f"download_{order_ref}_{i}",
                            use_container_width=True,
                        )
                except Exception as exc:
                    st.warning(f"Impossible de récupérer le livre {i} : {exc}")

            if st.button(
                "📦 Marquer comme expédiée",
                key=f"ship_{order_ref}",
                use_container_width=True,
            ):
                update_status(order, "SHIPPED")
                st.rerun()

        elif status == "SHIPPED":
            st.info("📦 Commande expédiée.")
            if st.button(
                "🎉 Marquer comme livrée",
                key=f"deliver_{order_ref}",
                use_container_width=True,
            ):
                update_status(order, "DELIVERED")
                st.rerun()

        elif status == "DELIVERED":
            st.success("🎉 Commande livrée.")

        elif status == "CANCELLED":
            st.error("Commande annulée.")

        with st.expander("🔎 Détails techniques"):
            st.write(f"**Commande Supabase :** {order_ref}")
            st.write(f"**Référence personnage Storage :** {order.get('reference_path', '—')}")
            st.write(f"**Couvertures Storage :** {order.get('cover_paths', [])}")
            st.write(f"**PDF Storage :** {order.get('generated_files', [])}")
            st.caption(
                "Les fichiers restent dans le bucket privé my-little-hero-files."
            )
            if order.get("last_error"):
                st.error(f"Dernière erreur : {order['last_error']}")


st.divider()
st.caption("🌟 My Little Hero — Tableau de bord interne")
