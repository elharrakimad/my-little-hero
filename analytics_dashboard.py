"""Private analytics view, mounted after the existing admin authentication."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import streamlit as st
from site_analytics import FUNNEL, load_events, summarize


def render_analytics(get_db):
    st.subheader('Flux du site · en direct')
    days = st.selectbox('Période', [1, 7], format_func=lambda n: 'Aujourd’hui' if n == 1 else '7 derniers jours')
    now = datetime.now(ZoneInfo('Africa/Casablanca'))
    start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)
    # Include the active-session window even immediately after midnight.
    since = min(start, now - timedelta(minutes=5))
    try:
        rows = load_events(get_db(), since.astimezone(timezone.utc).isoformat())
    except Exception:
        st.warning('Le suivi est indisponible. Vérifiez la connexion et l’installation de database/site_events.sql. Aucun chiffre fictif n’est affiché.')
        return
    period = [r for r in rows if datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')) >= start]
    stats = summarize(period)
    columns = st.columns(4)
    columns[0].metric('Sessions actives · 5 min', summarize(rows)['active'])
    columns[1].metric('Sessions sur la période', stats['visits'])
    columns[2].metric('Sessions avec clic WhatsApp', stats['whatsapp'])
    columns[3].metric('Erreurs d’aperçu', stats['errors'])
    st.caption('Actualisé à ' + now.strftime('%H:%M:%S') + ' · heure du Maroc. Une session correspond à un onglet du navigateur ; ce ne sont pas des personnes uniques.')
    if not period:
        st.info('Aucun événement reçu sur cette période. Les chiffres apparaîtront après activation du suivi sur le site.')
        return
    st.dataframe(stats['funnel'], hide_index=True, use_container_width=True)
    st.bar_chart(stats['funnel'], x='Étape', y='Sessions', horizontal=True)
    st.caption('Chaque étape du tableau compte les sessions ayant aussi atteint toutes les étapes précédentes. Les retours et nouvelles tentatives ne sont pas comptés comme de nouveaux visiteurs.')
    if stats['average_seconds'] is not None:
        st.metric('Durée moyenne des aperçus réussis', f"{stats['average_seconds']:.0f} s")
    st.caption('Un clic WhatsApp ne prouve ni l’envoi du message ni le paiement. Les paiements et livraisons restent consultables dans les vues commandes.')
    labels = dict(FUNNEL)
    recent = [r for r in reversed(period) if r['event_name'] != 'heartbeat'][:30]
    with st.expander('30 dernières actions anonymes'):
        st.dataframe([{'Heure': datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')).astimezone(ZoneInfo('Africa/Casablanca')).strftime('%d/%m %H:%M:%S'),
                       'Action': labels.get(r['event_name'], r['event_name']), 'Pack': r.get('pack_id')} for r in recent], hide_index=True, use_container_width=True)
