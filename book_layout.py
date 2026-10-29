"""Deterministic A4 storybook layout: all typography is typeset, never painted by AI."""
from dataclasses import dataclass, replace
from pathlib import Path
from html import escape
import math
import re
import reportlab
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph
from reportlab.lib.utils import ImageReader

LAYOUT_VERSION = "storybook-a4-v2"


@dataclass(frozen=True)
class KeepsakeLayout:
    congratulations_top: float = 742
    medal_bottom: float = 505
    medal_size: float = 180
    ribbon_top: float = 491
    ribbon_height: float = 28
    ribbon_width: float = 380
    ribbon_size: float = 12.5
    message_top: float = 450
    next_adventure_top: float = 392
    drawing_bottom: float = 100
    signature_y: float = 77


@dataclass(frozen=True)
class Layout:
    width: float = A4[0]
    height: float = A4[1]
    binding_margin: float = 62.36   # 22 mm
    outer_margin: float = 51.02     # 18 mm
    top_margin: float = 48.19       # 17 mm
    bottom_margin: float = 48.19
    title_band: float = 78
    footer_band: float = 28
    narrative_height: float = 130
    image_gap: float = 18
    title_size: float = 23
    title_leading: float = 27
    body_size: float = 14
    body_leading: float = 20
    souvenir_title_size: float = 28
    drawing_height: float = 250
    keepsake: KeepsakeLayout = KeepsakeLayout()

    @property
    def content_width(self):
        return self.width - self.binding_margin - self.outer_margin

    @property
    def center(self):
        return self.binding_margin + self.content_width / 2


DEFAULT_LAYOUT = Layout()


def register_fonts():
    folder = Path(reportlab.__file__).parent / "fonts"
    for name, file in (("MLHBody", "Vera.ttf"), ("MLHBold", "VeraBd.ttf")):
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(folder / file)))


def paragraph(text, *, size=14, leading=20, title=False):
    register_fonts()
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), ParagraphStyle(
        "MLH", fontName="Times-Bold" if title else "MLHBody", fontSize=size,
        leading=leading, alignment=1, textColor="black", splitLongWords=True,
        spaceBefore=0, spaceAfter=0))


def split_narrative(text, config=DEFAULT_LAYOUT):
    """Keep every word, fixed 14pt type and fixed image area; add continuation pages."""
    words = re.sub(r"\s+", " ", text).strip().split()
    if not words:
        raise ValueError("Le récit de la page est vide.")
    parts = []
    width = config.content_width - 14
    while words:
        low, high, best = 1, len(words), 0
        while low <= high:
            count = (low + high) // 2
            _, height = paragraph(" ".join(words[:count]), size=config.body_size,
                leading=config.body_leading).wrap(width, config.narrative_height)
            if height <= config.narrative_height:
                best, low = count, count + 1
            else:
                high = count - 1
        if best == 0:
            raise ValueError("Le récit ne tient pas dans la zone réservée à la taille minimale.")
        # Prefer a sentence boundary, but never discard any content.
        sentence_ends = [i for i in range(max(1, best // 2), best + 1)
            if re.search(r'[.!?…][»”"\']?$', words[i - 1])]
        if best < len(words) and sentence_ends:
            best = sentence_ends[-1]
        parts.append(" ".join(words[:best]))
        words = words[best:]
    return parts


def star(canvas, x, y, radius=5):
    path = canvas.beginPath()
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = radius if i % 2 == 0 else radius * .46
        point = (x + r * math.cos(angle), y + r * math.sin(angle))
        if i == 0: path.moveTo(*point)
        else: path.lineTo(*point)
    path.close()
    canvas.setStrokeColorRGB(0, 0, 0)
    canvas.setLineWidth(.7)
    canvas.drawPath(path, stroke=1, fill=0)


def draw_image(canvas, image, x, y, width, height):
    if not Path(image).exists():
        raise FileNotFoundError(image)
    source = ImageReader(str(image))
    w, h = source.getSize()
    scale = min(width / w, height / h)
    canvas.drawImage(source, x+(width-w*scale)/2, y+(height-h*scale)/2,
        width=w*scale, height=h*scale, mask="auto")


def draw_centered(canvas, text, top, width, *, center, size=14, leading=20, title=False, max_height=None):
    item = paragraph(text, size=size, leading=leading, title=title)
    _, height = item.wrap(width, 10000)
    if max_height is not None and height > max_height:
        raise ValueError(f"Texte trop long pour sa zone : {text[:70]}")
    item.drawOn(canvas, center-width/2, top-height)
    return height


def draw_story_page(canvas, title, text, image, number, config=DEFAULT_LAYOUT):
    x, w = config.binding_margin, config.content_width
    text_bottom = config.bottom_margin + config.footer_band
    image_bottom = text_bottom + config.narrative_height + config.image_gap
    image_top = config.height - config.top_margin - config.title_band
    # Reserve and measure narrative first. No font shrinking and no image overlap.
    narrative = paragraph(text, size=config.body_size, leading=config.body_leading)
    _, height = narrative.wrap(w-14, config.narrative_height)
    if height > config.narrative_height:
        raise ValueError("Récit non réparti avant la mise en page.")
    title_height = paragraph(title, size=config.title_size, leading=config.title_leading, title=True).wrap(w-20, 1000)[1]
    if title_height > config.title_band - 16:
        raise ValueError("Titre trop long : raccourcir le titre sans réduire sa police.")
    title_top = config.height-config.top_margin-12
    star(canvas, config.center-48, config.height-config.top_margin+5, 3)
    star(canvas, config.center, config.height-config.top_margin+8, 4)
    star(canvas, config.center+48, config.height-config.top_margin+5, 3)
    draw_centered(canvas, title, title_top, w-20, center=config.center,
        size=config.title_size, leading=config.title_leading, title=True,
        max_height=config.title_band-16)
    draw_image(canvas, image, x, image_bottom, w, image_top-image_bottom)
    narrative.drawOn(canvas, x+7, text_bottom+(config.narrative_height-height)/2)
    star(canvas, config.center, config.bottom_margin-12, 13)
    canvas.setFont("MLHBody", 9)
    canvas.drawCentredString(config.center, config.bottom_margin-15, str(number))
    canvas.showPage()


def souvenir_copy(name, gender="", language="Français"):
    if language == "English":
        return (f"Well done, {name}!", "Little hero, big imagination", "With your courage and your colors, you brought this adventure to life.", "Imagine your next adventure…", "Colored by:", "Date:")
    if language == "Español":
        return (f"¡Bravo, {name}!", "Pequeña heroína, gran imaginación" if gender == "girl" else "Pequeño héroe, gran imaginación", "Con tu valentía y tus colores, has dado vida a esta aventura.", "Imagina tu próxima aventura…", "Coloreado por:", "Fecha:")
    return (f"Bravo, {name} !", "Petite héroïne, grande imagination" if gender == "girl" else "Petit héros, grande imagination", "Avec ton courage et tes couleurs, tu as donné vie à cette aventure.", "Imagine ta prochaine aventure…", "Colorié par :", "Le :")


def draw_keepsake_page(canvas, name, congratulations, medal, *, gender="", language="Français", config=DEFAULT_LAYOUT):
    title, ribbon, message, next_adventure, colored_by, date = souvenir_copy(name, gender, language)
    x, w, center = config.binding_margin, config.content_width, config.center
    k = config.keepsake
    draw_centered(canvas, title, config.height-config.top_margin, w, center=center,
        size=config.souvenir_title_size, leading=34, title=True, max_height=68)
    draw_centered(canvas, congratulations, k.congratulations_top, w-26, center=center, size=config.body_size, leading=19, max_height=38)
    draw_image(canvas, medal, center-k.medal_size/2, k.medal_bottom, k.medal_size, k.medal_size)
    # Outline ribbon, with white fill only. Every inscription is actual PDF text.
    canvas.setLineWidth(.85)
    canvas.setFillColorRGB(1, 1, 1)
    path = canvas.beginPath()
    half = k.ribbon_width/2
    path.moveTo(center-half, k.ribbon_top); path.lineTo(center+half, k.ribbon_top)
    path.lineTo(center+half-9, k.ribbon_top-k.ribbon_height/2); path.lineTo(center+half, k.ribbon_top-k.ribbon_height)
    path.lineTo(center-half, k.ribbon_top-k.ribbon_height); path.lineTo(center-half+9, k.ribbon_top-k.ribbon_height/2); path.close()
    canvas.drawPath(path, stroke=1, fill=1)
    draw_centered(canvas, ribbon, k.ribbon_top-6, k.ribbon_width-38, center=center, size=k.ribbon_size, leading=16, max_height=20)
    draw_centered(canvas, message, k.message_top, w-36, center=center, size=config.body_size, leading=config.body_leading, max_height=40)
    draw_centered(canvas, next_adventure, k.next_adventure_top, w, center=center, size=20, leading=25, title=True, max_height=28)
    # A generous unruled drawing area, only its corners are decorated.
    drawing_bottom, drawing_top = k.drawing_bottom, k.drawing_bottom+config.drawing_height
    for xx, yy in ((x+10, drawing_bottom+8), (x+w-10, drawing_bottom+8),
                   (x+10, drawing_top-8), (x+w-10, drawing_top-8)):
        star(canvas, xx, yy, 5)
        star(canvas, xx+(-11 if xx>center else 11), yy+(-10 if yy>250 else 10), 2.5)
    canvas.setFillColorRGB(0, 0, 0)
    canvas.setFont("MLHBody", 11)
    canvas.drawString(x, k.signature_y, colored_by + " ____________")
    canvas.drawRightString(x+w, k.signature_y, date + " ____________")
    canvas.showPage()


def build_book_pdf(output, pages, medal, *, child_name, congratulations, gender="", language="Français", cover=None, config=DEFAULT_LAYOUT):
    register_fonts()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # The longest title defines one common band for the entire book, still at 23pt.
    titles = [p["title"] + " (suite)" for p in pages]
    title_height = max((paragraph(t, size=config.title_size, leading=config.title_leading,
        title=True).wrap(config.content_width-20, 10000)[1] for t in titles), default=0)
    config = replace(config, title_band=max(config.title_band, title_height+18))
    if config.height-config.top_margin-config.title_band-(config.bottom_margin+config.footer_band+config.narrative_height+config.image_gap) < 220:
        raise ValueError("Le titre ne laisse plus assez d'espace pour l'illustration.")
    canvas = Canvas(str(output), pagesize=(config.width, config.height), pageCompression=1)
    canvas.setTitle(f"{child_name} - livre de contes à colorier")
    canvas.setAuthor("My Little Hero")
    if cover:
        draw_image(canvas, cover, 0, 0, config.width, config.height)
        canvas.showPage()
    number = 0
    for page in pages:
        for part_number, text in enumerate(split_narrative(page["text"], config)):
            number += 1
            title = page["title"] + (" (suite)" if part_number else "")
            draw_story_page(canvas, title, text, page["image"], number, config)
    draw_keepsake_page(canvas, child_name, congratulations, medal, gender=gender, language=language, config=config)
    canvas.save()
    return output
