"""My Little Hero — moteur de génération d'un livre final.

Le titre est choisi une seule fois dans app.py puis transmis ici.
Le moteur force PAGE 1, la couverture et le PDF à utiliser exactement ce titre.
"""

from pathlib import Path
import re
import shutil

import generate_book as engine


def _safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9À-ÿ _-]", "", value).strip()
    value = re.sub(r"\s+", "_", value)
    return value[:80] or "livre"


def generate_book_from_adventure(
    *,
    child_name: str,
    age: int,
    theme: str,
    language: str,
    client_idea: str,
    child_quality: str,
    book_title: str,
    reference_path: str | Path,
    output_dir: str | Path,
    preview_cover_path: str | Path | None = None,
    child_gender: str = "",
    progress=None,
) -> Path:
    """Génère le livre complet d'une aventure avec un titre imposé."""
    if child_gender not in {"", "girl", "boy"}:
        raise ValueError("Genre invalide : utiliser girl ou boy.")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    final_pdf = output_dir / f"{_safe_filename(child_name)}_{_safe_filename(book_title)}.pdf"
    if final_pdf.exists() and final_pdf.stat().st_size > 0:
        print(f"⏭️ Livre déjà terminé, réutilisation : {final_pdf}")
        return final_pdf

    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    engine.NAME = child_name
    engine.AGE = int(age)
    engine.THEME = theme
    engine.LANGUAGE = language
    engine.CHILD_GENDER = child_gender
    engine.CLIENT_IDEA = client_idea or ""
    engine.CHILD_QUALITY = child_quality or ""
    engine.BOOK_TITLE = book_title.strip()

    engine.REFERENCE_IMAGE = str(Path(reference_path).resolve())
    engine.STORY_FILE = str(output_dir / "story.txt")

    # IMPORTANT:
    # generate_book.py / ReportLab peut refuser un WindowsPath lorsqu'il
    # est fourni comme nom de fichier. On transmet donc toujours des str.
    engine.PAGES_FOLDER = pages_dir
    engine.COVER_FILE = str(output_dir / "cover.png")
    engine.KEEPSAKE_IMAGE = str(output_dir / "keepsake_medallion_v2.png")
    engine.OUTPUT_FILE = str(final_pdf.with_suffix(".building.pdf"))

    engine.REUSE_EXISTING_FILES = True

    if not engine.BOOK_TITLE:
        raise ValueError("Titre de livre manquant.")

    print(f"📚 Titre définitif : {engine.BOOK_TITLE}")

    if not Path(engine.STORY_FILE).exists() or not Path(engine.STORY_FILE).stat().st_size:
        if progress:
            progress("story", "Rédaction de l'histoire", page_index=0, page_total=10)
        engine.generate_story()
    elif progress:
        progress("story", "Histoire existante conservée", page_index=0, page_total=10)

    generated_title = engine.get_book_title().strip()
    if generated_title != engine.BOOK_TITLE.strip():
        raise ValueError(
            "Le titre de PAGE 1 ne correspond pas au titre choisi dans l'aperçu."
        )

    engine.generate_all_pages(progress=progress)

    if preview_cover_path:
        preview_cover = Path(preview_cover_path)
        if not preview_cover.exists():
            raise FileNotFoundError(
                f"Couverture d'aperçu introuvable : {preview_cover}"
            )
        shutil.copy2(preview_cover, engine.COVER_FILE)
        print(f"🖼️ Couverture validée réutilisée : {preview_cover}")
    else:
        engine.generate_cover()

    if progress:
        progress("pdf", "Création du médaillon souvenir personnalisé", page_index=10, page_total=10)
    engine.generate_keepsake_medallion()
    if progress:
        progress("pdf", "Assemblage des pages et de la page souvenir dans le PDF", page_index=10, page_total=10)
    engine.generate_pdf()
    Path(engine.OUTPUT_FILE).replace(final_pdf)
    return final_pdf
