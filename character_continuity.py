"""Stable cast descriptions and reusable visual anchors; no extra AI calls."""
import json
from pathlib import Path
import re
from anime_cast import secondary_reference_path

CHILD_OUTFIT_INSTRUCTION = (
    "TENUE FIXE DE L’ENFANT POUR TOUTE L’HISTOIRE : lorsque l’enfant est dessiné, "
    "la couverture validée fait autorité pour sa tenue, même si la référence de son visage "
    "porte des vêtements neutres différents. Conserver exactement les mêmes haut, bas, "
    "manches, chaussures, gants, ceinture, cape, masque, coiffure et accessoires portés, "
    "avec les mêmes formes, coupes, longueurs, motifs et détails distinctifs. "
    "En noir et blanc, traduire les couleurs en zones blanches à colorier, sans changer "
    "les motifs ni remplir les vêtements. Ne pas inventer de changement de costume, "
    "uniforme, armure, transformation ou accessoire vestimentaire au fil des scènes. "
    "La pose et l’expression peuvent évoluer ; l’identité et la tenue restent identiques, "
    "y compris sur le médaillon final. Si aucune couverture n’est fournie, garder la tenue "
    "de la référence initiale de l’enfant."
)


def child_outfit_instruction(book_style="coloring"):
    if book_style == "colored":
        return CHILD_OUTFIT_INSTRUCTION.replace(
            "En noir et blanc, traduire les couleurs en zones blanches à colorier, sans changer les motifs ni remplir les vêtements.",
            "Conserver les couleurs exactes de la tenue de couverture, ses motifs et ses accessoires, sans changer de palette.")
    return CHILD_OUTFIT_INSTRUCTION

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


def cast_from_story(story, page_total=10, max_characters=6):
    parts = re.split(r"(?m)^\s*PERSONNAGES_JSON\s*$", story, maxsplit=1)
    if len(parts) == 1:
        return None  # Legacy stories keep their original text and illustrations.
    try:
        data = json.loads(parts[1].strip())
        rows = data["characters"]
        if not isinstance(rows, list) or len(rows) > max_characters:
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
        raise ValueError(f"Fiche des personnages invalide : maximum {max_characters} secondaires. Vérifier PERSONNAGES_JSON avant les illustrations.") from exc


def continuity_context(story, page_number, page_total=10, book_style="coloring"):
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
        + child_outfit_instruction(book_style) + "\n" + profiles + "\n" + present + "\nNe pas fusionner, échanger, rajeunir ou redessiner les identités. "
        "Les poses et expressions peuvent changer ; les visages, coiffures, silhouettes, tenues et accessoires restent fixes.")


def reference_paths(story, page_number, reference, cover, pages_folder, page_total=10, secondary_folder=None, book_style="coloring"):
    """Keep the child's image first; use first appearances instead of drifting copies."""
    result = [(Path(reference), "Identité prioritaire de l’enfant principal : conserver son visage et sa coiffure. Si la couverture est fournie, ses vêtements remplacent la tenue neutre de cette référence.")]
    if cover and Path(cover).is_file() and Path(cover).stat().st_size:
        result.append((Path(cover), "Couverture validée : référence prioritaire et immuable de la tenue de l’enfant, de ses chaussures et accessoires, ainsi que de l’univers et des secondaires visibles. Ignorer le texte ; conserver tous les motifs et détails de la tenue en contours noirs sur fond blanc."))
        if book_style == "colored":
            result[-1] = (result[-1][0], result[-1][1].replace("en contours noirs sur fond blanc", "avec exactement les mêmes couleurs"))
    cast = cast_from_story(story, page_total)
    if cast is None:
        anchors = list(range(1, min(page_number, page_total + 1)))
    else:
        target = min(page_number, page_total)
        if secondary_folder:
            for character in cast:
                if target in character["pages"]:
                    path = secondary_reference_path(secondary_folder, character)
                    if not path.is_file() or not path.stat().st_size:
                        raise FileNotFoundError(f"Référence du personnage {character['name']} introuvable.")
                    result.append((path, f"Référence dédiée prioritaire du personnage {character['id']} ({character['name']}) : conserver exactement cette identité, sa tenue et ses accessoires."))
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
