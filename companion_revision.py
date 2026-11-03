"""Owner-requested substantive companion redesign; no automatic model retries."""
import json
import re
from pathlib import Path
from book_content import story_pages

LUMO_APPEARANCE = (
    'A small turquoise quadruped with rounded ears, a short violet leaf-shaped crest, '
    'a violet feather-shaped tail, three white oval markings on each flank, '
    'round dark eyes and soft padded feet. Lumo releases gentle luminous pollen '
    'from its tail to illuminate paths and awaken plants. Its proportions, colors '
    'and markings stay identical on every page. No clothing or accessories.'
)


def revised_story(story):
    narrative, marker, metadata = story.partition('PERSONNAGES_JSON')
    if not marker:
        raise ValueError('Fiche des personnages manquante pour la nouvelle version.')
    cast = json.loads(metadata.strip())
    characters = cast['characters']
    if any(c['name'] == 'Lumo' and c['appearance'] == LUMO_APPEARANCE for c in characters):
        return story
    targets = [c for c in characters if c['name'] == 'Sparky']
    if len(targets) != 1:
        raise ValueError('Cette révision concerne uniquement le compagnon Sparky.')
    replacements = {
        'red cheeks glowed with excitement as the tiny yellow companion crackled softly':
            'violet tail shimmered with excitement as the turquoise companion scattered soft luminous pollen',
        'a small yellow creature with long pointed ears tipped in black, red cheeks, and a lightning-shaped tail':
            LUMO_APPEARANCE.rstrip('.'),
        'lightning-shaped tail': 'violet feather-shaped tail',
        'gentle golden spark': 'gentle swirl of luminous pollen',
        'gentle luminous electricity': 'soft luminous pollen',
        'glowing electricity': 'glowing pollen',
        'controlled ribbon of golden electricity': 'controlled ribbon of luminous pollen',
        'cheeks glowed like two tiny lamps': 'three white oval markings glowed softly',
        'steady golden glow': 'steady turquoise glow',
    }
    for old, new in replacements.items():
        narrative = narrative.replace(old, new)
    narrative = re.sub(r'\bSparky\b', 'Lumo', narrative)
    if re.search(r'yellow creature|yellow companion|red cheeks|lightning-shaped|electricity|ears tipped in black', narrative, re.I):
        raise ValueError('La révision nécessite encore une correction des descriptions du compagnon.')
    targets[0].update(name='Lumo', appearance=LUMO_APPEARANCE)
    result = narrative + marker + '\n' + json.dumps(cast, ensure_ascii=False)
    story_pages(result, 10)
    return result


def prepare_revision(engine, output_dir, language, progress=None):
    if language != 'English':
        raise ValueError('Cette révision préparée concerne le récit anglais existant.')
    folder = Path(output_dir)
    path = Path(engine.STORY_FILE)
    original = path.read_text(encoding='utf-8')
    updated = revised_story(original)
    if updated != original:
        if any((folder/'pages').glob('page_*.png')):
            raise ValueError('Des illustrations existent déjà : révision manuelle nécessaire avant remplacement.')
        backup = folder/'story_before_companion_revision.txt'
        if not backup.exists():
            engine.atomic_write_bytes(backup, original.encode('utf-8'))
        engine.atomic_write_bytes(path, updated.encode('utf-8'))
    # The former cover may depict the previous companion: never reuse it.
    engine.COVER_FILE = str(folder/'cover_lumo_v1.png')
    if not Path(engine.COVER_FILE).exists():
        if progress:
            progress('illustrations', 'Nouvelle couverture avec le compagnon original Lumo', page_index=0, page_total=10)
        engine.generate_cover()
