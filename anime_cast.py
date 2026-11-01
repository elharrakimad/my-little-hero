"""Anime-specific cast policy, resolved from the same catalogue as the website."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path


@lru_cache(maxsize=1)
def anime_themes():
    source = (Path(__file__).resolve().parent / "theme-catalog.js").read_text(encoding="utf-8")
    data = source.split("window.MLH_THEME_CATALOG =", 1)[1].lstrip()
    rows, _ = json.JSONDecoder().raw_decode(data)
    return frozenset(value for row in rows if row["category"] == "anime"
        for value in (row["theme"], row["label"], row["ar"]))


def is_anime_theme(theme):
    return str(theme).strip() in anime_themes()


def cast_limit(theme):
    return 2 if is_anime_theme(theme) else 6


def anime_cast_instruction(theme, book_style="coloring"):
    if not is_anime_theme(theme):
        return ""
    instruction = ("RÈGLE ANIME : l’enfant est le héros principal. Deux personnages secondaires au maximum "
        "dans tout le livre, couverture comprise, et pas seulement par page. Ce total inclut amis, "
        "compagnons, animaux, créatures et adversaires. Aucun figurant supplémentaire, foule, "
        "silhouette humaine ou nouveau personnage anonyme. Ils ne sont présents que si la scène "
        "le demande. Pour chacun, fixer visage, âge apparent, coiffure, silhouette, tenue, chaussures, "
        "accessoires et détails caractéristiques de son univers anime, lisibles en noir et blanc. "
        "Ne jamais transformer l’enfant principal en un personnage secondaire.")
    return instruction.replace("lisibles en noir et blanc", "cohérents en couleur") if book_style == "colored" else instruction


def secondary_reference_folder(theme, pages_folder):
    return Path(pages_folder).parent / "secondary_references" if is_anime_theme(theme) else None


def secondary_reference_path(folder, character):
    # Identity and appearance are part of the key; changed profiles never reuse stale images.
    identity = json.dumps({k: character[k] for k in ("id", "name", "appearance")}, ensure_ascii=False, sort_keys=True)
    key = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
    return Path(folder) / f"character_{key}.png"
