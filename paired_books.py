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


def color_to_lineart(source, target):
    """Deterministic black outlines: same characters, framing and scene, no AI."""
    from PIL import Image, ImageFilter, ImageOps
    with Image.open(source) as original:
        gray = ImageOps.grayscale(original)
        smooth = gray.filter(ImageFilter.GaussianBlur(1.2))
        edges = smooth.filter(ImageFilter.FIND_EDGES)
        thick = edges.filter(ImageFilter.MaxFilter(3))
        ink = thick.point(lambda value: 0 if value > 18 else 255)
        # FIND_EDGES leaves unfiltered border pixels; remove this artifact only.
        ink.paste(255, (0, 0, ink.width, 1))
        ink.paste(255, (0, ink.height-1, ink.width, ink.height))
        ink.paste(255, (0, 0, 1, ink.height))
        ink.paste(255, (ink.width-1, 0, ink.width, ink.height))
        ink.save(target, format='PNG')
        for image in (gray, smooth, edges, thick, ink):
            image.close()


def build_paired_coloring(source_dir, output_dir, output_pdf, *, progress=None):
    """Ten image-only A4 pages. Never write visible text, cover or keepsake."""
    from book_content import story_pages
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen.canvas import Canvas
    from PIL import Image
    source_dir, output_dir, output_pdf = map(Path, (source_dir, output_dir, output_pdf))
    story = (source_dir/'story.txt').read_bytes()
    story_pages(story.decode('utf-8'), 10)  # Validate the exact source story.
    sources = [source_dir/'pages'/f'page_{i:02d}.png' for i in range(1, 11)]
    if any(not p.is_file() or not p.stat().st_size for p in sources):
        raise FileNotFoundError('Illustrations couleur manquantes : aucune autre histoire ne sera générée.')
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = output_dir/'pages'
    pages.mkdir(exist_ok=True)
    manifest = {'version': PAIR_VERSION, 'story_sha256': hashlib.sha256(story).hexdigest(),
                'source_images': [hashlib.sha256(p.read_bytes()).hexdigest() for p in sources]}
    previous_path = output_dir/'paired_manifest.json'
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    (output_dir/'story.txt').write_bytes(story)
    for index, source in enumerate(sources, 1):
        target = pages/f'page_{index:02d}.png'
        if previous != manifest or not target.is_file() or not target.stat().st_size:
            color_to_lineart(source, target)
        if progress:
            progress('illustrations', f'Même scène {index}/10 convertie en coloriage sans texte',
                     page_index=index, page_total=10)
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
