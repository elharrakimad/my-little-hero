"""Private production dashboard. All progress comes from worker checkpoints."""
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo
import streamlit as st
from production_status import STAGES

LABELS = {"WAITING_FOR_PAYMENT": "Paiement à vérifier", "PAID": "En file d'attente",
    "GENERATING": "En production", "GENERATION_INTERRUPTED": "À reprendre",
    "BOOKS_READY": "Livres prêts", "SHIPPED": "Expédiée", "DELIVERED": "Livrée", "CANCELLED": "Annulée"}


def local_time(value):
    if not value:
        return "—"
    try:
        date = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if date.tzinfo is None:
            date = date.replace(tzinfo=ZoneInfo("UTC"))
        return date.astimezone(ZoneInfo("Africa/Casablanca")).strftime("%d/%m à %H:%M:%S")
    except (ValueError, TypeError):
        return "—"


def render_progress(order):
    status = order.get("status")
    progress = order.get("generation_progress") or {}
    ready = status in {"BOOKS_READY", "SHIPPED", "DELIVERED"}
    percent = 100 if ready else min(99, max(0, int(progress.get("percent", 0))))
    label = "Production terminée" if ready else "Reprise en file d'attente" if status == "PAID" else progress.get("label") or ("Production interrompue" if status == "GENERATION_INTERRUPTED" else "En attente du démarrage")
    st.progress(percent, text=label)
    current = progress.get("failed_stage") if progress.get("stage") == "error" else progress.get("stage")
    keys = [key for key, _ in STAGES]
    index = keys.index(current) if current in keys else -1
    stages = []
    for number, (key, label) in enumerate(STAGES):
        state = "done" if ready or number < index else "active" if number == index else "pending"
        if number == index and status == "GENERATION_INTERRUPTED":
            state = "failed"
        stages.append(f'<div class="mlh-step {state}"><span>{number+1:02d}</span>{escape(label)}</div>')
    st.markdown('<div class="mlh-steps">'+''.join(stages)+'</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.caption(f"Livre {progress.get('book_index', 1)} / {order.get('adventure_count', 1)}")
    page_total = progress.get("page_total", 10)
    b.caption(f"Illustrations terminées : {progress.get('page_index', 0)} / {page_total}" if progress else "Détails disponibles au prochain passage du moteur")
    c.caption(f"Dernière activité : {local_time(progress.get('updated_at'))}")
    if status == "GENERATING" and progress.get("updated_at"):
        last = datetime.fromisoformat(progress["updated_at"].replace("Z", "+00:00"))
        age = (datetime.now(last.tzinfo) - last).total_seconds()
        if age > 300:
            st.warning("Aucune nouvelle étape depuis plus de 5 minutes. Un appel IA peut encore être en cours ; ne relancez pas une seconde production.")
    if status == "GENERATION_INTERRUPTED":
        if progress.get("error"):
            st.error(progress["error"])
            st.caption("Les étapes terminées sont conservées. La reprise réutilise les fichiers existants.")
        else:
            st.warning("Ancienne interruption : le détail n'était pas enregistré. Le prochain passage du moteur activera le suivi détaillé.")
    history = progress.get("history") or []
    if history:
        with st.expander("Journal de production · événements horodatés"):
            st.dataframe([{"Heure (Maroc)": local_time(item.get("at")), "Étape": item.get("stage", ""),
                "Événement": item.get("message", "")} for item in reversed(history)], hide_index=True, use_container_width=True)


def show_dashboard(list_orders, get_db, download_pdf, update_status):
    st.markdown("""<style>
    .stApp{background:#f5f6fa;color:#20283b}
    [data-testid="stSidebar"]{background:#121a2b}
    [data-testid="stSidebar"] *{color:#e8edf7}
    [data-testid="stSidebar"] [data-testid="stButton"] button{background:#25314c;border-color:#3c4861;color:#e8edf7}
    [data-testid="stSidebar"] input{color:#20283b!important}
    .block-container{max-width:1300px;padding-top:2rem}
    .mlh-header{padding:28px 32px;border-radius:18px;background:linear-gradient(120deg,#19223b,#343560);color:white;margin-bottom:26px}
    .mlh-header small{letter-spacing:.16em;color:#bfc5ee;font-weight:700}
    .mlh-header h1{color:white;font-size:32px;margin:6px 0}
    .mlh-header p{margin:0;color:#d2d8eb}
    [data-testid="stVerticalBlockBorderWrapper"]{background:white;border-radius:16px}
    [data-testid="stMetric"]{background:white;padding:18px;border-radius:14px;border:1px solid #e4e7ef}
    .mlh-order-title{font-size:22px;font-weight:750;margin:0 0 4px}
    .mlh-ref{font-size:12px;color:#69758b;word-break:break-all}
    .mlh-badge{display:inline-block;background:#edf0f8;color:#36415b;padding:6px 12px;border-radius:99px;font-weight:700;font-size:12px}
    .mlh-badge.GENERATION_INTERRUPTED{background:#fff0e9;color:#9b3c1f}
    .mlh-badge.BOOKS_READY{background:#e3f5ec;color:#176548}
    .mlh-badge.GENERATING{background:#ece9ff;color:#5140ae}
    .mlh-steps{display:grid;grid-template-columns:repeat(6,1fr);gap:7px;margin:15px 0}
    .mlh-step{font-size:11px;border-top:3px solid #e5e8f0;padding:8px 3px;color:#8790a3}
    .mlh-step span{display:block;font-size:10px;font-weight:750;margin-bottom:4px}
    .mlh-step.done{border-color:#2b9871;color:#237354}
    .mlh-step.active{border-color:#7060d8;color:#5140ae;font-weight:700}
    .mlh-step.failed{border-color:#d2714c;color:#9b3c1f;font-weight:700}
    @media(max-width:650px){.mlh-steps{grid-template-columns:repeat(3,1fr)}.mlh-header{padding:22px}.mlh-header h1{font-size:26px}}
    </style>""", unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### MY LITTLE HERO")
        st.caption("CENTRE DE PRODUCTION")
        view = st.radio("Espace", ["Toutes les commandes", "Paiements", "Production", "Incidents", "Livres prêts"], label_visibility="collapsed")
        search = st.text_input("Rechercher", placeholder="Prénom ou référence")
        auto = st.toggle("Actualisation automatique", value=True)
        st.caption("Toutes les 5 secondes pendant que cette page est ouverte.")
        if st.button("Actualiser maintenant", use_container_width=True):
            st.rerun()
        st.divider()
        st.caption("Espace privé • accès propriétaire")
        if st.button("Se déconnecter", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.rerun()
    st.markdown('<div class="mlh-header"><small>MY LITTLE HERO / ATELIER</small><h1>Centre de production</h1><p>Vérifiez les paiements. Suivez chaque livre, de l’histoire au PDF.</p></div>', unsafe_allow_html=True)

    @st.fragment(run_every=5 if auto else None)
    def live_orders():
        try:
            orders = list_orders()
        except Exception:
            st.error("Les commandes sont momentanément indisponibles. Vérifiez la connexion Supabase et réessayez.")
            return
        metrics = st.columns(4)
        for col, label, statuses in zip(metrics, ["Paiements à vérifier", "En file / production", "À reprendre", "Livres disponibles"],
            [{"WAITING_FOR_PAYMENT"}, {"PAID", "GENERATING"}, {"GENERATION_INTERRUPTED"}, {"BOOKS_READY", "SHIPPED", "DELIVERED"}]):
            col.metric(label, sum(o.get("status") in statuses for o in orders))
        st.caption("Vue synchronisée à " + datetime.now(ZoneInfo("Africa/Casablanca")).strftime("%H:%M:%S") + " · heure du Maroc")
        allowed = {"Paiements": {"WAITING_FOR_PAYMENT"}, "Production": {"PAID", "GENERATING"},
            "Incidents": {"GENERATION_INTERRUPTED"}, "Livres prêts": {"BOOKS_READY", "SHIPPED", "DELIVERED"}}.get(view)
        filtered = [o for o in orders if (not allowed or o.get("status") in allowed) and
            (not search or search.casefold() in (str(o.get("child_name", ""))+" "+o["order_ref"]).casefold())]
        st.subheader(f"{len(filtered)} commande(s)")
        if not filtered:
            st.info("Aucune commande dans cette vue.")
        for order in filtered:
            ref, status = order["order_ref"], order.get("status", "")
            with st.container(border=True):
                left, right = st.columns([3, 1])
                with left:
                    st.markdown(f'<div class="mlh-order-title">{escape(str(order.get("child_name") or "Sans prénom"))}</div><div class="mlh-ref">{escape(ref)} · {local_time(order.get("created_at"))}</div>', unsafe_allow_html=True)
                with right:
                    st.markdown(f'<span class="mlh-badge {status if status in LABELS else ""}">{escape(LABELS.get(status, status))}</span>', unsafe_allow_html=True)
                    st.write(f"**{order.get('price', '—')} DH**")
                st.caption(f"{order.get('pack', '—')} · {order.get('age', '—')} ans · {order.get('language', '—')} · {order.get('adventure_count', 1)} aventure(s)")
                for adventure in order.get("adventures", []):
                    st.write(f"**{adventure.get('title') or 'Titre à préciser'}** — {adventure.get('theme', '')}")
                if status == "WAITING_FOR_PAYMENT":
                    st.info("La couverture est enregistrée. La génération complète attend votre validation du paiement.")
                    confirmed = st.checkbox("J’ai vérifié le paiement reçu ou les conditions convenues.", key=f"payment_{ref}")
                    if st.button("Valider le paiement et lancer la production", key=f"validate_{ref}", disabled=not confirmed, type="primary"):
                        (get_db().table("orders").update({"status": "PAID"}).eq("order_ref", ref).eq("status", "WAITING_FOR_PAYMENT").execute())
                        st.rerun()
                elif status == "PAID":
                    st.info("Commande en file d’attente. Le serveur la prendra en charge automatiquement ; vous pouvez fermer cette page.")
                    render_progress(order)
                else:
                    render_progress(order)
                if status == "GENERATION_INTERRUPTED":
                    if st.button("Reprendre à la dernière étape enregistrée", key=f"resume_{ref}", type="primary"):
                        (get_db().table("orders").update({"status": "PAID"}).eq("order_ref", ref).eq("status", "GENERATION_INTERRUPTED").execute())
                        st.rerun()
                if order.get("generated_files"):
                    for index, path in enumerate(order["generated_files"], 1):
                        if st.button(f"Préparer le téléchargement du livre {index}", key=f"prepare_{ref}_{index}"):
                            try:
                                pdf = download_pdf(order, index, path)
                                st.session_state[f"pdf_{ref}_{index}"] = (pdf.read_bytes(), pdf.name)
                            except Exception:
                                st.error("Impossible de récupérer ce PDF. Réessayez dans quelques instants.")
                        data = st.session_state.get(f"pdf_{ref}_{index}")
                        if data:
                            st.download_button(f"Télécharger le livre {index}", data=data[0], file_name=data[1], mime="application/pdf", key=f"download_{ref}_{index}")
                with st.expander("Détails de la commande"):
                    st.write("Téléphone :", order.get("customer_phone") or "Non renseigné")
                    st.write("E-mail :", order.get("customer_email") or "Non renseigné")
                    st.caption("Création : " + local_time(order.get("created_at")))
                if status == "BOOKS_READY" and st.button("Marquer comme expédiée", key=f"ship_{ref}"):
                    update_status(order, "SHIPPED")
                    st.rerun()
                if status == "SHIPPED" and st.button("Marquer comme livrée", key=f"deliver_{ref}"):
                    update_status(order, "DELIVERED")
                    st.rerun()
    live_orders()
