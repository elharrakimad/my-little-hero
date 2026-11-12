"""Two formats of the same story, explicitly enabled on new bundle orders only."""
import hashlib
import json
from pathlib import Path

PAIR_VERSION = 'same-scenes-v1'
PAIRED_PACKS = frozenset({'Super Héros', 'Ultimate Hero'})


def is_paired_coloring(order, index, adventure):
    if adventure.get('paired_version') != PAIR_VERSION:
        return False  # Preserve existing/legacy orders exactly as they were sold.
    if (order.get('pack') not in PAIRED_PACKS or index != 2
            or adventure.get('shared_story_from') != 1
            or adventure.get('book_style') != 'coloring'
            or not adventure.get('image_only')):
        raise ValueError('Association de livres invalide.')
    source = order['adventures'][0]
    if source.get('book_style') != 'colored' or any(
            source.get(key) != adventure.get(key) for key in ('title', 'theme', 'idea')):
        raise ValueError('Les deux formats doivent partager la même histoire.')
    return True


RENDER_VERSION = 'clean-redraw-v2'

CLEAN_LINEART_PROMPT = """Redessine l'illustration fournie en VRAIE PAGE DE COLORIAGE POUR ENFANT.
L'image fournie fait autorité pour la scène : conserve les mêmes personnages,
leurs visages reconnaissables, leurs vêtements, leurs positions, leurs gestes,
les objets importants et l'action. Ne crée pas une nouvelle histoire.
{scene}

Il faut un dessin propre de coloriste professionnel, PAS un filtre de contours.
Traits noirs lisses, continus, assez épais et réguliers sur fond blanc pur.
Grandes zones BLANCHES fermées et faciles à remplir au crayon. Cheveux et
vêtements restent blancs à l'intérieur de leurs contours. Simplifie fortement
les textures et les petits éléments du décor en quelques formes lisibles.
Aucune ombre, aucun aplat noir, aucun gris, aucun dégradé, aucun grain,
aucun pointillé, aucune hachure, aucune trame, aucune texture de papier.
Supprime tous les détails minuscules et les reflets inutiles. Le personnage
principal doit être immédiatement lisible et le décor rester secondaire.
Composition verticale pleine page, sans cadre ni marge de mise en page.
Aucun texte, lettre, numéro, titre, logo, signature ou filigrane.
"""


def validate_clean_lineart(image):
    """Reject shading and pepper noise; do not turn a colored image into edges."""
    from PIL import ImageFilter, ImageChops
    gray = image.convert('L')
    total = gray.width * gray.height
    histogram = gray.histogram()
    if sum(histogram[64:240]) / total > .12:
        gray.close()
        raise ValueError('Coloriage refusé : ombres ou niveaux de gris trop importants.')
    ink = gray.point(lambda value: 0 if value < 180 else 255)
    gray.close()
    black = ink.histogram()[0] / total
    median = ink.filter(ImageFilter.MedianFilter(3))
    specks = ImageChops.subtract(median, ink)
    noise = sum(specks.histogram()[1:]) / total
    median.close()
    specks.close()
    if not .003 <= black <= .25 or noise > .02:
        ink.close()
        raise ValueError('Coloriage refusé : dessin trop chargé, trop vide ou bruité. Révision requise.')
    return ink


def color_to_lineart(source, target, *, scene='', client=None):
    """Redraw from the exact colored scene, then validate; never use FIND_EDGES."""
    import base64
    import io
    from PIL import Image
    if client is None:
        from openai import OpenAI
        client = OpenAI(timeout=240, max_retries=0)
    with Path(source).open('rb') as reference:
        result = client.images.edit(model='gpt-image-2', image=[reference],
            prompt=CLEAN_LINEART_PROMPT.format(scene=scene), size='1024x1536', quality='medium')
    raw = base64.b64decode(result.data[0].b64_json)
    temporary = Path(target).with_suffix('.building.png')
    try:
        with Image.open(io.BytesIO(raw)) as image:
            cleaned = validate_clean_lineart(image)
            try:
                cleaned.save(temporary, format='PNG')
            finally:
                cleaned.close()
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def build_paired_coloring(source_dir, output_dir, output_pdf, *, progress=None, review_page=None):
    """Ten image-only A4 pages. Never write visible text, cover or keepsake."""
    from book_content import story_pages
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen.canvas import Canvas
    from PIL import Image
    source_dir, output_dir, output_pdf = map(Path, (source_dir, output_dir, output_pdf))
    if review_page is not None and (type(review_page) is not int or not 1 <= review_page <= 10):
        raise ValueError('Page de contrôle invalide.')
    story = (source_dir/'story.txt').read_bytes()
    scenes = story_pages(story.decode('utf-8'), 10)  # Exact same story, not rewritten.
    sources = [source_dir/'pages'/f'page_{i:02d}.png' for i in range(1, 11)]
    if any(not p.is_file() or not p.stat().st_size for p in sources):
        raise FileNotFoundError('Illustrations couleur manquantes : aucune autre histoire ne sera générée.')
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = output_dir/'pages'
    pages.mkdir(exist_ok=True)
    manifest = {'version': PAIR_VERSION, 'renderer': RENDER_VERSION, 'story_sha256': hashlib.sha256(story).hexdigest(),
                'source_images': [hashlib.sha256(p.read_bytes()).hexdigest() for p in sources]}
    previous_path = output_dir/'paired_manifest.json'
    (output_dir/'story.txt').write_bytes(story)
    for index, source in enumerate(sources, 1):
        if review_page is not None and index != review_page:
            continue
        target = pages/f'page_{index:02d}.png'
        checkpoint = pages/f'page_{index:02d}.verified.json'
        expected = {'renderer': RENDER_VERSION, 'source_sha256': manifest['source_images'][index-1],
                    'story_sha256': manifest['story_sha256']}
        saved = json.loads(checkpoint.read_text()) if checkpoint.exists() else {}
        reusable = (target.is_file() and target.stat().st_size and saved.get('source') == expected
                    and saved.get('output_sha256') == hashlib.sha256(target.read_bytes()).hexdigest())
        if not reusable:
            if progress:
                progress('illustrations', f'Redessin propre de la même scène {index}/10, sans texte',
                         page_index=index-1, page_total=10)
            color_to_lineart(source, target, scene=scenes[index-1]['scene'])
            temp_checkpoint = checkpoint.with_suffix('.tmp')
            temp_checkpoint.write_text(json.dumps({'source': expected,
                'output_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}), encoding='utf-8')
            temp_checkpoint.replace(checkpoint)
        if progress:
            progress('illustrations', f'Coloriage propre {index}/10 vérifié',
                     page_index=index, page_total=10)
    if review_page is not None:
        return pages/f'page_{review_page:02d}.png'
    temporary = output_pdf.with_suffix('.building.pdf')
    width, height = A4
    try:
        canvas = Canvas(str(temporary), pagesize=A4, pageCompression=1)
        for index in range(1, 11):
            path = pages/f'page_{index:02d}.png'
            with Image.open(path) as image:
                w, h = image.size
            scale = max(width/w, height/h)
            canvas.saveState()
            clip = canvas.beginPath()
            clip.rect(0, 0, width, height)
            canvas.clipPath(clip, stroke=0, fill=0)
            canvas.drawImage(str(path), (width-w*scale)/2, (height-h*scale)/2,
                             width=w*scale, height=h*scale)
            canvas.restoreState()
            canvas.showPage()
        canvas.save()
        temporary.replace(output_pdf)
        temp_manifest = previous_path.with_suffix('.tmp')
        temp_manifest.write_text(json.dumps(manifest), encoding='utf-8')
        temp_manifest.replace(previous_path)
    finally:
        temporary.unlink(missing_ok=True)
    return output_pdf
