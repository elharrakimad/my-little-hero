"""Anonymous event validation and session-based reporting; no personal fields."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

EVENTS = {'page_view', 'heartbeat', 'creation_started', 'pack_selected',
          'hero_completed', 'adventure_selected', 'preview_started',
          'preview_succeeded', 'preview_failed', 'whatsapp_clicked'}
FUNNEL = [('page_view', 'Visite'), ('creation_started', 'Création démarrée'),
          ('hero_completed', 'Héros renseigné'), ('adventure_selected', 'Aventure validée'),
          ('preview_succeeded', 'Aperçu réussi'), ('whatsapp_clicked', 'Clic WhatsApp')]


def validate_event(payload):
    if not isinstance(payload, dict) or set(payload) - {'event_id', 'session_id', 'event_name', 'pack_id', 'duration_ms'}:
        raise ValueError('Événement invalide')
    if payload.get('event_name') not in EVENTS:
        raise ValueError('Événement inconnu')
    row = {key: str(UUID(str(payload.get(key, '')))) for key in ('event_id', 'session_id')}
    row['event_name'] = payload['event_name']
    for key, maximum in [('pack_id', 5), ('duration_ms', 3600000)]:
        value = payload.get(key)
        if value is not None:
            if type(value) is not int or not (1 if key == 'pack_id' else 0) <= value <= maximum:
                raise ValueError('Valeur invalide')
            row[key] = value
    return row


def load_events(db, since):
    rows, offset = [], 0
    # Stable ordering and fixed end prevent pagination drifting during refresh.
    end = datetime.now(timezone.utc).isoformat()
    while True:
        batch = (db.table('site_events').select('*').gte('created_at', since)
                 .lte('created_at', end).order('created_at').order('event_id')
                 .range(offset, offset + 999).execute()).data or []
        rows.extend(batch)
        if len(batch) < 1000:
            return rows
        offset += 1000


def summarize(rows, now=None):
    now = now or datetime.now(timezone.utc)
    sessions = {name: set() for name in EVENTS}
    active, durations = set(), []
    for row in rows:
        name, session = row['event_name'], row['session_id']
        if name not in sessions:
            continue
        sessions[name].add(session)
        at = datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))
        if now - timedelta(minutes=5) <= at <= now:
            active.add(session)
        if name == 'preview_succeeded' and row.get('duration_ms') is not None:
            durations.append(row['duration_ms'] / 1000)
    # Each stage must have been reached in the same session as all prior stages.
    cohort, funnel, previous = set(sessions['page_view']), [], None
    for name, label in FUNNEL:
        cohort &= sessions[name]
        count = len(cohort)
        funnel.append({'Étape': label, 'Sessions': count,
                       'Abandons depuis l’étape précédente': None if previous is None else previous - count})
        previous = count
    return {'active': len(active), 'visits': len(sessions['page_view']), 'funnel': funnel,
            'errors': sum(r['event_name'] == 'preview_failed' for r in rows),
            'average_seconds': sum(durations) / len(durations) if durations else None,
            'whatsapp': len(sessions['whatsapp_clicked'])}
