"""Read the existing French-labelled story contract, preserving all narrative text."""
import re


def story_pages(story, count=10):
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
    block = re.split(r"(?im)^\s*SOUVENIR\s*$", story, maxsplit=1)
    if len(block) == 2:
        match = re.search(r"F[eé]licitations\s*:\s*([^\n]+)", block[1], re.I)
        if match and len(match[1].strip()) <= 110:
            return match[1].strip()
    if language == "English":
        return "You completed your mission with courage and imagination!"
    if language == "Español":
        return "¡Has cumplido tu misión con valentía e imaginación!"
    if "basket" in theme.casefold():
        return "Tu as mené ton équipe jusqu’au panier décisif. Bravo pour ton courage !"
    return "Tu as accompli ta mission avec courage et imagination !"
