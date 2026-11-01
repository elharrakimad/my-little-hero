"""Read the existing French-labelled story contract, preserving all narrative text."""
import re


def normalize_story_structure(story):
    """Canonicalize technical labels only; never translate narrative or cast data."""
    labels = {
        "Titre": r"Titre|Title|Título|Titulo|العنوان",
        "Texte": r"Texte|Text|Texto|النص",
        "Scène à illustrer": r"Sc[eè]ne à illustrer|Scene to illustrate|Escena a ilustrar|المشهد المراد رسمه",
        "Félicitations": r"F[eé]licitations|Congratulations|Felicitaciones|التهنئة",
    }
    # Metadata is opaque: a character description may contain similar words.
    narrative, marker, metadata = story.partition("PERSONNAGES_JSON")
    for canonical, aliases in labels.items():
        narrative = re.sub(
            rf"(?im)^[ \t]*(?:{aliases})[ \t]*[:：][ \t]*(?:\r?\n[ \t]*)?",
            lambda match: canonical + " : ", narrative)
    return narrative + marker + metadata


def story_pages(story, count=10):
    story = normalize_story_structure(story)
    narrative = re.split(r"(?im)^\s*SOUVENIR\s*$", story, maxsplit=1)[0]
    chunks = re.split(r"(?im)^\s*PAGE\s+(\d+)\s*$", narrative)
    sections = {int(chunks[i]): chunks[i+1] for i in range(1, len(chunks), 2)}
    pages = []
    for number in range(1, count+1):
        match = re.search(r"Titre\s*:\s*(.*?)\s*Texte\s*:\s*(.*?)\s*Sc[eè]ne à illustrer\s*:\s*(.*)",
            sections.get(number, ""), re.I | re.S)
        if not match or not all(part.strip() for part in match.groups()):
            raise ValueError(f"La page {number} doit contenir un titre, un récit et une scène.")
        pages.append(dict(number=number, title=match[1].strip(),
            text=re.sub(r"\s+", " ", match[2]).strip(), scene=match[3].strip()))
    return pages


def keepsake_congratulations(story, theme="", language="Français"):
    story = normalize_story_structure(story)
    block = re.split(r"(?im)^\s*SOUVENIR\s*$", story, maxsplit=1)
    if len(block) == 2:
        match = re.search(r"F[eé]licitations\s*:\s*([^\n]+)", block[1], re.I)
        if match and len(match[1].strip()) <= 110:
            return match[1].strip()
    if language == "English":
        return "You completed your mission with courage and imagination!"
    if language == "Español":
        return "¡Has cumplido tu misión con valentía e imaginación!"
    if language == "العربية":
        return "لقد أنجزت مهمتك بشجاعة وخيال!"
    if "basket" in theme.casefold():
        return "Tu as mené ton équipe jusqu’au panier décisif. Bravo pour ton courage !"
    return "Tu as accompli ta mission avec courage et imagination !"
