"""Stable cast descriptions and reusable visual anchors; no extra AI calls."""
import json
from pathlib import Path
import re

CAST_INSTRUCTIONS = """
PERSONNAGES SECONDAIRES RÉCURRENTS
Définis une seule apparence immuable pour chaque compagnon, animal ou adversaire :
âge apparent, visage, coiffure, silhouette, vêtements, chaussures, accessoires,
et marques distinctives visibles en noir et blanc. Conserve ces traits dans toutes
les scènes. Utilise toujours le même nom et le même identifiant pour un personnage.
Limite la distribution à six personnages secondaires identifiables au maximum.
Précise exactement qui est présent dans chaque scène ; les autres restent absents.
Après le bloc SOUVENIR et sa phrase de félicitations, ajoute PERSONNAGES_JSON sur
une ligne, puis un objet JSON valide, sans balises Markdown, de cette structure :
{"characters":[{"id":"ami_1","name":"Nom","appearance":"Description visuelle fixe et détaillée",
"pages":[1,3,5,10]}]}
La liste pages contient exactement les numéros où ce personnage est dessiné,
de 1 à 10. Inclus aussi les personnages qui n’apparaissent qu’une fois. N’inclus
pas l’enfant principal dans cette liste. Si aucun secondaire, characters vaut [].
Ces métadonnées ne font pas partie du texte imprimé du livre.
"""


def cast_from_story(story, page_total=10):
    parts = re.split(r"(?m)^\s*PERSONNAGES_JSON\s*$", story, maxsplit=1)
    if len(parts) == 1:
        return None  # Legacy stories keep their original text and illustrations.
    try:
        data = json.loads(parts[1].strip())
        rows = data["characters"]
        if not isinstance(rows, list) or len(rows) > 6:
            raise ValueError
        ids = set()
        for row in rows:
            if not all(isinstance(row.get(k), str) and row[k].strip() for k in ("id", "name", "appearance")):
                raise ValueError
            if row["id"] in ids:
                raise ValueError
            ids.add(row["id"])
            pages = row["pages"]
            if not isinstance(pages, list) or not pages or any(type(n) is not int or not 1 <= n <= page_total for n in pages):
                raise ValueError
        return rows
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ValueError("Fiche des personnages invalide : vérifier PERSONNAGES_JSON avant les illustrations.") from exc


def continuity_context(story, page_number, page_total=10):
    cast = cast_from_story(story, page_total)
    if cast is None:
        # Old stories already contain the appearance notes; reuse them verbatim.
        scenes = re.findall(r"Sc[eè]ne à illustrer\s*:\s*(.*?)(?=\n\s*PAGE\s+\d+|\n\s*SOUVENIR|$)", story, re.S | re.I)
        profiles = "\n".join(f"Scène {i}: {scene.strip()}" for i, scene in enumerate(scenes, 1))
        present = "Dessiner uniquement les personnages de la scène actuelle."
    else:
        profiles = "\n".join(f'{c["id"]} — {c["name"]} : {c["appearance"]}' for c in cast)
        present_ids = [c["id"] for c in cast if min(page_number, page_total) in c["pages"]]
        present = "Secondaires présents dans cette scène : " + (", ".join(present_ids) or "aucun")
    return ("FICHE COMMUNE DES PERSONNAGES (identités fixes, ne pas imprimer ce texte) :\n"
        + profiles + "\n" + present + "\nNe pas fusionner, échanger, rajeunir ou redessiner les identités. "
        "Les poses et expressions peuvent changer ; les visages, coiffures, silhouettes, tenues et accessoires restent fixes.")


def reference_paths(story, page_number, reference, cover, pages_folder, page_total=10):
    """Keep the child's image first; use first appearances instead of drifting copies."""
    result = [(Path(reference), "Identité prioritaire de l’enfant principal : conserver son visage et sa coiffure.")]
    if cover and Path(cover).is_file() and Path(cover).stat().st_size:
        result.append((Path(cover), "Couverture validée : apparence des personnages déjà visibles, tenues et univers ; ignorer son texte et ses couleurs pour le coloriage."))
    cast = cast_from_story(story, page_total)
    if cast is None:
        anchors = list(range(1, min(page_number, page_total + 1)))
    else:
        target = min(page_number, page_total)
        anchors = sorted({min(c["pages"]) for c in cast if target in c["pages"] and min(c["pages"]) < page_number})
    for number in anchors:
        path = Path(pages_folder) / f"page_{number:02d}.png"
        if path.is_file() and path.stat().st_size:
            result.append((path, f"Page {number} déjà dessinée : référence visuelle fixe des secondaires qui y apparaissent. Ne pas copier sa composition ni son action."))
    unique = []
    for path, role in result:
        if path.resolve() not in [p.resolve() for p, _ in unique]:
            unique.append((path, role))
    return unique


def reference_roles(references):
    return "\n".join(f"Image {i}: {role}" for i, (_, role) in enumerate(references, 1))
