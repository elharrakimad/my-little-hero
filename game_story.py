"""Shared opening for video-game adventures, resolved from the public catalogue."""
from functools import lru_cache
import json
from pathlib import Path


@lru_cache(maxsize=1)
def game_themes():
    source = (Path(__file__).parent / "theme-catalog.js").read_text(encoding="utf-8")
    rows, _ = json.JSONDecoder().raw_decode(source.split("window.MLH_THEME_CATALOG =", 1)[1].lstrip())
    return frozenset(value.strip() for row in rows if row["category"] == "video-games"
        for value in (row["theme"], row["label"], row["ar"]))


def game_story_instruction(theme):
    if str(theme).strip() not in game_themes():
        return ""
    return (
        "OUVERTURE OBLIGATOIRE DES HISTOIRES DE JEUX VIDÉO : "
        "La PAGE 1 commence dans le monde réel. L’enfant découvre une console de jeu "
        "mystérieuse, l’allume, puis sa lumière ouvre un passage qui le transporte "
        "dans le monde du jeu choisi. Raconter explicitement cette découverte et ce "
        "transport dans le texte de la PAGE 1, dans la langue demandée. "
        "La scène illustrée de la PAGE 1 représente l’enfant, la console et le passage "
        "lumineux vers cet univers ; son visage reste conforme à sa référence et sa tenue "
        "reste celle de la couverture. À partir de la PAGE 2, il est dans le monde "
        "sélectionné et vit la mission du thème choisi : décors, activités et défis "
        "doivent correspondre à ce jeu, pas à un autre. La console est un objet fictif, "
        "sans marque ni logo. Cette ouverture fait partie des dix scènes existantes, "
        "sans ajouter de page ou modifier les marqueurs techniques. "
        "Varier les lieux de découverte, les dialogues et les péripéties d’un livre "
        "à l’autre, mais conserver toujours cette découverte puis ce transport. "
        "Respecter le prénom, l’âge, le genre, la langue et les demandes du client "
        "dans la suite de l’aventure, ainsi que les identités et tenues fixes."
    )
