"""Offline PDF rebuild for storage limits. This module never calls an AI service."""
from pathlib import Path
from book_content import story_pages, keepsake_congratulations
from book_layout import build_book_pdf
from story_language import validate_printed_language


def is_payload_too_large(error):
    return "413" in str(error) and ("too large" in str(error).lower() or "maximum allowed size" in str(error).lower())


def optimize_saved_pdf(pdf_path, order, adventure, force_layout=False):
    if adventure.get('paired_version'):
        raise ValueError('Le cahier sans texte ne doit pas utiliser la mise en page avec récit.')
    pdf_path = Path(pdf_path)
    folder = pdf_path.parent
    story = (folder/"story.txt").read_text(encoding="utf-8")
    validate_printed_language(story, order["language"], 10)
    pages = story_pages(story, 10)
    for page in pages:
        page["image"] = folder/"pages"/f"page_{page['number']:02d}.png"
    medal, cover = folder/"keepsake_medallion_v2.png", folder/"cover.png"
    for path in [medal, cover, *(p["image"] for p in pages)]:
        if not path.is_file() or not path.stat().st_size:
            raise FileNotFoundError("Optimisation impossible : un fichier conservé est absent. Aucune génération IA ne sera lancée.")
    candidate = pdf_path.with_suffix(".optimized.pdf")
    try:
        build_book_pdf(candidate, pages, medal, child_name=order["child_name"],
            congratulations=keepsake_congratulations(story, adventure["theme"], order["language"]),
            gender=adventure.get("child_gender", ""), language=order["language"], cover=cover,
            book_style=adventure.get("book_style", "coloring"),
            narrative_background=folder/"narrative_background_v1.png")
        if force_layout or candidate.stat().st_size < pdf_path.stat().st_size:
            candidate.replace(pdf_path)
    finally:
        candidate.unlink(missing_ok=True)
    return pdf_path
