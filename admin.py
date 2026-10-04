import json
import os
from datetime import datetime
from pathlib import Path
import re
import urllib.parse

import streamlit as st

from book_engine import generate_book_from_adventure

# ============================================================
# MY LITTLE HERO — ADMIN
# Suivi des commandes / paiement / génération des livres
# ============================================================

st.set_page_config(
    page_title="My Little Hero — Admin",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

ORDERS_DIR = Path("orders")
DEFAULT_ADMIN_PASSWORD = ""

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
# AUTHENTIFICATION ADMIN
# ------------------------------------------------------------

def get_admin_password():
    """Use ADMIN_PASSWORD environment variable in local development.
    Streamlit secrets can also be used when deployed.
    """
    password = os.getenv("MY_LITTLE_HERO_ADMIN_PASSWORD", "")
    if password:
        return password

    try:
        return st.secrets.get("MY_LITTLE_HERO_ADMIN_PASSWORD", "")
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

def order_file(order_dir: Path) -> Path:
    return order_dir / "order.json"


def load_order(order_dir: Path):
    path = order_file(order_dir)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("preview_id", order_dir.name.replace("preview_", ""))
        return data
    except Exception as exc:
        return {"_error": str(exc), "preview_id": order_dir.name.replace("preview_", "")}


def save_order(order_dir: Path, order: dict):
    # _dir est utilisé uniquement en mémoire par l'interface Admin.
    # Path n'est pas sérialisable en JSON, donc on ne doit jamais l'enregistrer.
    data = dict(order)
    data.pop("_dir", None)

    order_file(order_dir).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_orders():
    if not ORDERS_DIR.exists():
        return []

    result = []
    for directory in ORDERS_DIR.glob("preview_*"):
        if not directory.is_dir() or not order_file(directory).exists():
            continue
        order = load_order(directory)
        order["_dir"] = directory
        result.append(order)

    result.sort(
        key=lambda x: order_file(x["_dir"]).stat().st_mtime,
        reverse=True,
    )
    return result


def format_date(order_dir: Path):
    try:
        timestamp = order_file(order_dir).stat().st_mtime
        return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "—"


def display_order_number(order, order_dir):
    value = order.get("order_number")
    if value:
        return str(value)
    return order.get("preview_id", order_dir.name)


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
    order["status"] = status
    order["updated_at"] = datetime.now().isoformat(timespec="seconds")
    save_order(order["_dir"], order)


def _safe_filename(value: str) -> str:
    """Convert a title/name into a safe Windows filename fragment."""
    import re
    value = re.sub(r"[^A-Za-z0-9À-ÿ _-]", "", str(value)).strip()
    value = re.sub(r"\s+", "_", value)
    return value[:80] or "livre"


def generate_order(order):
    """Generate all adventures using the titles already stored in order.json."""
    order_dir = order["_dir"]
    reference_path = Path(order["reference_path"])

    if not reference_path.exists():
        raise FileNotFoundError(f"Référence personnage introuvable : {reference_path}")

    if not order.get("adventures"):
        raise ValueError("Aucune aventure dans cette commande.")

    final_dir = order_dir / "final_books"
    final_dir.mkdir(parents=True, exist_ok=True)

    # Reprendre les livres déjà terminés. Important : si la génération
    # s'arrête au livre 2 (crédit API, erreur réseau, etc.), le livre 1
    # ne doit jamais être régénéré au prochain clic.
    generated_files = [
        str(Path(p).resolve())
        for p in order.get("generated_files", [])
        if Path(p).exists()
    ]
    total = len(order["adventures"])

    for index, adventure in enumerate(order["adventures"], start=1):
        title = (adventure.get("title") or "").strip()
        if not title:
            raise ValueError(f"Le titre de l'aventure {index} est manquant.")

        preview_cover = order_dir / f"cover_{index:02d}.png"
        if not preview_cover.exists():
            raise FileNotFoundError(f"Couverture {index} introuvable : {preview_cover}")

        adventure_dir = final_dir / f"adventure_{index:02d}"
        st.write(f"**{index}/{total} — {title}**")

        # Si cette aventure est déjà terminée, on la saute.
        expected_pdf = adventure_dir / (
            f"{_safe_filename(order['child_name'])}_{_safe_filename(title)}.pdf"
        )
        if expected_pdf.exists() and expected_pdf.stat().st_size > 0:
            pdf_path = expected_pdf
            st.info(f"⏭️ {index}/{total} déjà terminé — aucune régénération.")
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
                preview_cover_path=preview_cover,
            )

        pdf_string = str(Path(pdf_path).resolve())
        if pdf_string not in generated_files:
            generated_files.append(pdf_string)

        # Sauvegarder immédiatement après chaque livre réussi. Ainsi une
        # panne au livre suivant ne fait pas perdre le travail déjà terminé.
        order["generated_files"] = generated_files
        order["updated_at"] = datetime.now().isoformat(timespec="seconds")
        save_order(order_dir, order)

    order["generated_files"] = generated_files
    order["status"] = "BOOKS_READY"
    order["updated_at"] = datetime.now().isoformat(timespec="seconds")
    save_order(order_dir, order)

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
    .order-card {
        background: white;
        border: 1px solid #ececf4;
        border-radius: 20px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 7px 24px rgba(30,30,60,.06);
    }
    .metric-card {
        background: #fff;
        border: 1px solid #ececf4;
        border-radius: 18px;
        padding: 15px;
        text-align: center;
    }
    .small { color:#777; font-size:13px; }
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

orders = list_orders()

# ------------------------------------------------------------
# FILTRES / STATISTIQUES
# ------------------------------------------------------------

status_filter = st.selectbox(
    "Filtrer les commandes",
    ["Toutes"] + list(STATUS_LABELS.keys()),
    format_func=lambda value: "Toutes" if value == "Toutes" else STATUS_LABELS[value],
)

filtered = orders if status_filter == "Toutes" else [o for o in orders if o.get("status") == status_filter]

counts = {status: sum(o.get("status") == status for o in orders) for status in STATUS_LABELS}

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
    order_dir = order["_dir"]
    status = order.get("status", "WAITING_FOR_PAYMENT")
    badge = STATUS_BADGES.get(status, "⚪")

    with st.container(border=True):
        top1, top2 = st.columns([3, 1])
        with top1:
            st.markdown(
                f"### {badge} {order.get('child_name', 'Sans nom')} — "
                f"{order.get('pack', '?')} aventure(s)"
            )
            st.caption(
                f"Commande : `{display_order_number(order, order_dir)}`  •  "
                f"Créée/modifiée : {format_date(order_dir)}"
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
            st.write(f"📚 **Aventures :** {len(order.get('adventures', []))}")

        phone = order.get("customer_phone", "")
        email = order.get("customer_email", "")
        wa = whatsapp_link(phone)
        if phone:
            if wa:
                st.markdown(f"📱 **WhatsApp parent :** [{phone}]({wa})")
            else:
                st.write(f"📱 **Téléphone parent :** {phone}")
        else:
            st.caption("📱 Aucun numéro WhatsApp enregistré pour cette commande.")

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

        # Aperçu des couvertures : pas de photo enfant affichée ici.
        cover_files = [order_dir / f"cover_{i:02d}.png" for i in range(1, len(adventures) + 1)]
        existing_covers = [p for p in cover_files if p.exists()]
        if existing_covers:
            cols = st.columns(min(3, len(existing_covers)))
            for i, cover in enumerate(existing_covers):
                with cols[i % len(cols)]:
                    st.image(str(cover), caption=f"Couverture {i+1}", use_container_width=True)

        st.markdown("---")

        # ----------------------------------------------------
        # ACTIONS PAIEMENT
        # ----------------------------------------------------
        if status == "WAITING_FOR_PAYMENT":
            st.warning("💳 Vérifie le virement bancaire avant de confirmer le paiement.")
            confirm = st.checkbox(
                "☑️ J'ai vérifié le paiement et le montant reçu correspond à la commande.",
                key=f"confirm_payment_{order['preview_id']}",
            )
            if st.button(
                "✅ Confirmer le paiement",
                key=f"paid_{order['preview_id']}",
                type="primary",
                disabled=not confirm,
                use_container_width=True,
            ):
                update_status(order, "PAID")
                st.success("Paiement confirmé. La commande est prête à être générée.")
                st.rerun()

        # ----------------------------------------------------
        # ACTIONS GENERATION
        # ----------------------------------------------------
        elif status in ("PAID", "GENERATING", "GENERATION_INTERRUPTED"):
            # Un statut GENERATING peut rester enregistré si Streamlit, le PC
            # ou le processus Python a été arrêté pendant la production.
            # On autorise donc toujours une reprise ici. generate_order()
            # détecte les PDF déjà terminés et les saute.
            if status == "PAID":
                st.success("💳 Paiement vérifié. Tu peux maintenant lancer la production.")
            elif status == "GENERATING":
                st.warning("⚙️ Cette commande était en cours de génération lorsque le processus s'est arrêté.")
                st.caption("Tu peux reprendre la production : les livres déjà terminés seront ignorés.")
            else:
                st.warning("⚠️ La production a été interrompue. Tu peux la reprendre sans régénérer les livres déjà terminés.")
                if order.get("last_error"):
                    st.caption(f"Dernière erreur : {order['last_error']}")

            button_label = "🚀 Générer les livres" if status == "PAID" else "🔄 Reprendre la production"
            if st.button(
                button_label,
                key=f"generate_{order['preview_id']}",
                type="primary",
                use_container_width=True,
            ):
                try:
                    order["status"] = "GENERATING"
                    order.pop("last_error", None)
                    save_order(order_dir, order)
                    st.info("La production est lancée. Les livres déjà terminés seront ignorés.")
                    generated = generate_order(order)
                    st.success(f"✅ {len(generated)} livre(s) prêt(s).")
                    st.rerun()
                except Exception as exc:
                    # Une erreur pendant la production ne doit jamais faire
                    # perdre les livres déjà terminés. generate_order()
                    # sauvegarde generated_files après chaque livre réussi.
                    order["status"] = "GENERATION_INTERRUPTED"
                    order["last_error"] = str(exc)
                    order["updated_at"] = datetime.now().isoformat(timespec="seconds")
                    save_order(order_dir, order)
                    st.error(f"❌ La génération a été interrompue : {exc}")


        elif status == "BOOKS_READY":
            st.success("📕 Les livres sont prêts.")

            generated_files = order.get("generated_files", [])
            if generated_files:
                for i, file_name in enumerate(generated_files, start=1):
                    path = Path(file_name)
                    if path.exists():
                        st.download_button(
                            f"📥 Télécharger le livre {i}",
                            data=path.read_bytes(),
                            file_name=path.name,
                            mime="application/pdf",
                            key=f"download_{order['preview_id']}_{i}",
                            use_container_width=True,
                        )
                    else:
                        st.warning(f"Fichier introuvable : {path}")

            if st.button(
                "📦 Marquer comme expédiée",
                key=f"ship_{order['preview_id']}",
                use_container_width=True,
            ):
                update_status(order, "SHIPPED")
                st.rerun()

        elif status == "SHIPPED":
            st.info("📦 Commande expédiée.")
            if st.button(
                "🎉 Marquer comme livrée",
                key=f"deliver_{order['preview_id']}",
                use_container_width=True,
            ):
                update_status(order, "DELIVERED")
                st.rerun()

        elif status == "DELIVERED":
            st.success("🎉 Commande livrée.")

        elif status == "CANCELLED":
            st.error("Commande annulée.")

        # ----------------------------------------------------
        # ACTIONS SECONDAIRES
        # ----------------------------------------------------
        with st.expander("🔎 Détails techniques"):
            st.write(f"**Dossier :** `{order_dir}`")
            st.write(f"**Référence commande interne :** `{order.get('preview_id', order_dir.name)}`")
            st.write(f"**Référence personnage :** `{order.get('reference_path', '—')}`")
            st.write(f"**Téléphone parent :** `{order.get('customer_phone', '—')}`")
            st.write(f"**E-mail parent :** `{order.get('customer_email', '—')}`")
            if order.get("last_error"):
                st.error(f"Dernière erreur : {order['last_error']}")

st.divider()
st.caption("🌟 My Little Hero — Tableau de bord interne")
