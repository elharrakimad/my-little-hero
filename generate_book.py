from openai import OpenAI
import base64
import hashlib
import html
import re
from pathlib import Path
from child_profile import gender_instruction
from book_layout import build_book_pdf
from book_content import story_pages, keepsake_congratulations

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Image, Paragraph, Spacer, PageBreak,
    HRFlowable, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader


# ============================================================
# CONFIGURATION DU LIVRE
# ============================================================

NAME = ""
AGE = 9
THEME = ""
LANGUAGE = ""
CHILD_GENDER = ""

# Champs facultatifs du client
CLIENT_IDEA = ""
CHILD_QUALITY = ""

# Titre unique de l’aventure, généré à partir de l’histoire.
BOOK_TITLE = ""

# Photo/référence déjà validée pour le prototype.
# Pour la version Streamlit, ce chemin sera remplacé par la photo du client
# puis une référence sera générée automatiquement.
PHOTO_FILE = "enfant.jpg"
REFERENCE_IMAGE = "character_reference.png"

# Dossiers/fichiers
STORY_FILE = "story.txt"
PAGES_FOLDER = Path("pages")
COVER_FILE = "cover.png"
OUTPUT_FILE = f"{NAME}_Livre_Personnalise.pdf"
KEEPSAKE_IMAGE = "keepsake_medallion_v2.png"

NUMBER_OF_PAGES = 10

# Protection contre les dépenses inutiles.
# Si les paramètres du livre changent, les anciennes pages sont supprimées
# automatiquement pour éviter de mélanger deux histoires différentes.
REUSE_EXISTING_FILES = True


# ============================================================
# CLIENT OPENAI
# ============================================================

client = OpenAI()


# ============================================================
# OUTILS
# ============================================================

def file_signature():
    photo_hash = ""
    photo_path = Path(PHOTO_FILE)

    if photo_path.exists():
        photo_hash = hashlib.sha256(photo_path.read_bytes()).hexdigest()

    data = "|".join([
        NAME, str(AGE), THEME, LANGUAGE, CHILD_GENDER, CLIENT_IDEA, CHILD_QUALITY,
        "dynamic_title_v2", BOOK_TITLE.strip(), photo_hash
    ])

    return hashlib.sha256(data.encode("utf-8")).hexdigest()


SIGNATURE_FILE = Path(".book_signature")


def prepare_project():
    PAGES_FOLDER.mkdir(parents=True, exist_ok=True)

    current_signature = file_signature()
    previous_signature = (
        SIGNATURE_FILE.read_text(encoding="utf-8").strip()
        if SIGNATURE_FILE.exists()
        else ""
    )

    same_configuration = (
        REUSE_EXISTING_FILES
        and previous_signature == current_signature
        and Path(STORY_FILE).exists()
        and Path(REFERENCE_IMAGE).exists()
        and Path(COVER_FILE).exists()
    )

    if same_configuration:
        print("♻️ Même configuration détectée : fichiers existants réutilisés.")
        return True

    if previous_signature and previous_signature != current_signature:
        print("🔄 Nouvelle configuration/photo détectée.")
        print("🧹 Nettoyage des anciens fichiers générés...")

        for image in PAGES_FOLDER.glob("page_*.png"):
            image.unlink(missing_ok=True)

        Path(COVER_FILE).unlink(missing_ok=True)
        Path(STORY_FILE).unlink(missing_ok=True)
        Path(REFERENCE_IMAGE).unlink(missing_ok=True)

    SIGNATURE_FILE.write_text(current_signature, encoding="utf-8")
    return False


def require_file(path, message):
    if not Path(path).exists():
        raise FileNotFoundError(message)


def atomic_write_bytes(path, data):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


# ============================================================
# 1. CRÉATION DE LA RÉFÉRENCE DU PERSONNAGE
# ============================================================

def generate_character_reference():
    print("\n" + "=" * 60)
    print("👤 ÉTAPE 1/5 — CRÉATION DU PERSONNAGE DE RÉFÉRENCE")
    print("=" * 60)

    if REUSE_EXISTING_FILES and Path(REFERENCE_IMAGE).exists():
        print(f"⏭️ Référence déjà existante : {REFERENCE_IMAGE}")
        return

    require_file(
        PHOTO_FILE,
        f"❌ Photo de l'enfant introuvable : {PHOTO_FILE}"
    )

    photo = None

    try:
        photo = open(PHOTO_FILE, "rb")

        prompt = f"""
{gender_instruction(CHILD_GENDER)}
Crée une référence visuelle cohérente du personnage principal d'un
livre jeunesse personnalisé.

Utilise la photo fournie uniquement comme référence visuelle de l'enfant.

L'enfant s'appelle {NAME} et a {AGE} ans.

Transforme l'enfant en personnage principal correspondant au thème :
{THEME}

IMPORTANT :
- conserver les traits généraux du visage
- conserver la coiffure et l'apparence générale reconnaissable
- respecter l'âge apparent de l'enfant
- créer un personnage original
- adapter les vêtements et accessoires au thème
- style illustration jeunesse professionnelle
- composition verticale
- personnage visible en entier
- arrière-plan simple
- aucune personne célèbre
- aucun personnage ou univers protégé
- aucun texte, logo ou watermark

Cette image servira de référence pour toutes les illustrations du livre.
"""

        result = client.images.edit(
            model="gpt-image-2",
            image=[photo],
            prompt=prompt,
            size="1024x1536",
            quality="medium"
        )

        image_base64 = result.data[0].b64_json
        atomic_write_bytes(REFERENCE_IMAGE,
            base64.b64decode(image_base64)
        )

        print(f"✅ Référence créée : {REFERENCE_IMAGE}")

    finally:
        if photo is not None:
            photo.close()


# ============================================================
# 2. GÉNÉRATION DE L'HISTOIRE

# ============================================================

def generate_story():
    print("\n" + "=" * 60)
    print("📖 ÉTAPE 2/5 — GÉNÉRATION DE L'HISTOIRE")
    print("=" * 60)

    prompt = f"""
{gender_instruction(CHILD_GENDER)}
Tu es un auteur professionnel spécialisé dans les livres
personnalisés pour enfants.

Crée une histoire originale de 10 pages.

INFORMATIONS SUR L'ENFANT
- Prénom : {NAME}
- Âge : {AGE} ans
- Thème : {THEME}
- Langue : {LANGUAGE}

PERSONNALISATION DEMANDÉE PAR LE CLIENT
- Idée précise du client : {CLIENT_IDEA if CLIENT_IDEA else "Aucune idée précise. Invente librement une aventure adaptée à l'enfant."}
- Qualité ou élément à mettre en avant chez l'enfant : {CHILD_QUALITY if CHILD_QUALITY else "Aucune demande particulière. Fais ressortir naturellement une qualité positive adaptée à l'histoire."}

IMPORTANT :
Si une idée du client est fournie, elle doit devenir un élément important
de l'aventure et être intégrée naturellement dans l'intrigue.
Ne copie pas simplement l'idée mot pour mot : développe-la et enrichis-la.

Si aucune idée n'est fournie, invente toi-même une aventure originale.

Si une qualité de l'enfant est fournie, montre cette qualité à travers
ses actions et ses décisions plutôt que de simplement la mentionner.

PERSONNAGE PRINCIPAL
L'enfant doit être le personnage principal de l'histoire, héros ou héroïne selon le choix indiqué.
Son prénom doit apparaître naturellement dans l'histoire.

OBJECTIF
Créer une histoire amusante, captivante, éducative et adaptée à l'âge
de l'enfant, qui pourra ensuite être transformée en livre illustré
et en livre de coloriage.

L'histoire doit donner envie à l'enfant de lire la page suivante,
tout en lui faisant découvrir naturellement une valeur, une idée,
un mot nouveau ou une petite leçon adaptée à son âge.

RÈGLES DE L'HISTOIRE
- L'histoire doit être totalement originale.
- Aucun personnage connu ou protégé par le droit d'auteur.
- Aucun univers provenant d'un film, jeu vidéo, série ou livre existant.
- L'histoire doit avoir un début, un développement et une conclusion.
- Le personnage principal doit rencontrer un problème ou une mission.
- Il doit rencontrer des obstacles.
- L'enfant doit utiliser son courage, son intelligence ou son imagination
  pour résoudre le problème.
- La conclusion doit être positive.
- Pas de violence graphique.
- Le vocabulaire doit être adapté à un enfant de {AGE} ans.
- Chaque page doit faire avancer l'aventure.
- Intègre progressivement une valeur éducative : courage, entraide,
  patience, créativité, persévérance, respect, confiance, etc.
- Ne transforme pas l'histoire en leçon scolaire.
- La morale doit être naturelle et liée à l'aventure.
- Ajoute, lorsque cela s'intègre bien, un petit élément de curiosité
  ou de réflexion pour encourager l'enfant à réfléchir.
- Évite les phrases trop longues ou les mots trop difficiles.

STRUCTURE

Crée exactement 10 pages.

IMPORTANT — TITRE IMPOSÉ DU LIVRE :

Le titre définitif du livre a déjà été choisi avant la génération.

Titre définitif :
{BOOK_TITLE}

N'invente PAS de nouveau titre.

Utilise EXACTEMENT ce titre, caractère par caractère, pour le champ
« Titre » de la PAGE 1.

Le titre doit être exactement :
{BOOK_TITLE}

Ne le modifie pas.
Ne le reformule pas.
Ne change pas les majuscules ou minuscules.
N'ajoute aucun point, symbole ou autre texte.

Les pages 2 à 10 peuvent avoir leurs propres titres.

Pour chaque page, utilise exactement ce format :

PAGE 1
Titre :
Texte :
Scène à illustrer :

PAGE 2
Titre :
Texte :
Scène à illustrer :

Continue jusqu'à PAGE 10.

TEXTE
Le texte de chaque page doit contenir environ 2 à 4 phrases, idéalement
35 à 65 mots, sans dépasser 80 mots. N'appauvris pas le sens de la scène.
Il doit être suffisamment court pour être placé facilement
sur une page illustrée.

Le texte doit être vivant et amusant, avec des descriptions
simples, des émotions et quelques dialogues courts lorsque
cela améliore l'histoire.

Évite de répéter le prénom de l'enfant à chaque phrase.
Le récit doit sembler être une vraie histoire pour enfants,
pas une liste d'événements.

SCÈNE À ILLUSTRER
Décris précisément la scène qui devra être dessinée.

Pour chaque scène, indique si possible :
- le personnage principal
- son apparence générale
- sa position
- son action
- les personnages secondaires
- le décor
- les objets importants
- l'ambiance

Les scènes doivent être adaptées à des illustrations
de livre de coloriage en noir et blanc.

IMPORTANT POUR LA COHÉRENCE
Le personnage principal doit rester visuellement cohérent
d'une page à l'autre.

Ne change pas son âge, son apparence générale,
sa coiffure ou ses caractéristiques principales
entre les différentes scènes.

À LA FIN DE L'HISTOIRE
La PAGE 10 doit terminer l'aventure avec une conclusion positive
et mémorable.

Ajoute dans la PAGE 10 une petite phrase de type :
"Le petit secret de [prénom] : ..."
ou une courte leçon/curiosité liée à l'aventure.

Cette phrase doit rester amusante et adaptée à l'âge de l'enfant.

N'ajoute aucune explication avant ou après l'histoire.
Commence directement par PAGE 1.
Après la scène de PAGE 10, ajoute ce bloc distinct, sans nouvelle page d'histoire :
SOUVENIR
Félicitations : une phrase de 110 caractères maximum qui félicite l'enfant
pour la mission réellement accomplie. Rédige cette phrase dans {LANGUAGE}.
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt
    )

    story = response.output_text

    atomic_write_bytes(STORY_FILE, story.encode("utf-8"))

    print(story)
    print("\n✅ Histoire enregistrée dans story.txt")


# ============================================================
# 2. GÉNÉRATION DES 10 ILLUSTRATIONS
# ============================================================

def get_page(story, page_number):
    story = re.split(r"(?im)^\s*SOUVENIR\s*$", story, maxsplit=1)[0]
    pattern = rf"PAGE\s+{page_number}(.*?)(?=PAGE\s+{page_number + 1}|$)"
    match = re.search(
        pattern, story, re.IGNORECASE | re.DOTALL
    )
    return match.group(1).strip() if match else None


def extract_scene(page_content):
    match = re.search(
        r"Scène à illustrer\s*:\s*(.*?)(?=\n\s*PAGE\s+\d+|$)",
        page_content,
        re.IGNORECASE | re.DOTALL
    )
    return match.group(1).strip() if match else page_content


def extract_title(page_content):
    match = re.search(
        r"Titre\s*:\s*(.*?)(?=\n|$)",
        page_content,
        re.IGNORECASE
    )
    return match.group(1).strip() if match else ""



def extract_book_title(story):
    """Le titre principal est le Titre de la PAGE 1."""
    page_one = get_page(story, 1)
    if not page_one:
        return ""

    title = extract_title(page_one)

    # Évite un titre vide ou un titre trop générique.
    if title and title.lower() not in {
        "l'aventure de " + NAME.lower(),
        "une aventure de " + NAME.lower(),
    }:
        return title.strip()

    return title.strip()


def get_book_title():
    story = Path(STORY_FILE).read_text(encoding="utf-8")
    title = extract_book_title(story)

    if not title:
        raise ValueError("Impossible de récupérer le titre de l'aventure dans story.txt.")

    return title



def generate_page(page_number, page_content):
    filename = PAGES_FOLDER / f"page_{page_number:02d}.png"

    if REUSE_EXISTING_FILES and filename.exists():
        print(
            f"⏭️ Page {page_number} existe déjà, "
            f"on passe à la suivante : {filename}"
        )
        return

    title = extract_title(page_content)
    scene = extract_scene(page_content)

    print(f"\n🎨 Génération de la page {page_number}...")
    print(f"📖 Titre : {title}")
    print(f"🎬 Scène : {scene[:300]}...")

    require_file(
        REFERENCE_IMAGE,
        f"❌ Image de référence introuvable : {REFERENCE_IMAGE}"
    )

    reference_image = None

    try:
        reference_image = open(REFERENCE_IMAGE, "rb")

        prompt = f"""
{gender_instruction(CHILD_GENDER)}
Crée une illustration verticale pour un livre de coloriage
personnalisé destiné aux enfants.

IMPORTANT :
Utilise l'image fournie comme référence du personnage principal.

Le personnage principal doit rester visuellement cohérent
avec l'image de référence :
- même visage général
- même coiffure
- mêmes caractéristiques physiques générales
- même âge apparent
- même apparence générale

Le personnage principal est l'enfant décrit dans la scène.
Respecte strictement son apparence de référence et les éléments
visuels établis dans les pages précédentes.

Si des personnages secondaires récurrents apparaissent dans la scène,
conserve également leur apparence de manière cohérente.

THÈME DU LIVRE :
{THEME}

SCÈNE À ILLUSTRER :
{scene}

OBJECTIF DE L'ILLUSTRATION
L'image doit représenter clairement et principalement
la scène décrite ci-dessus.

Ne remplace pas la scène par une autre scène et n'ajoute pas
d'éléments narratifs importants qui ne sont pas décrits.

Le personnage principal doit être facilement identifiable.
La composition doit raconter visuellement l'action de la scène.
Les expressions doivent être adaptées à l'émotion de la scène.
Le décor doit correspondre au thème de l'histoire.

STYLE
- illustration de livre de coloriage pour enfants
- noir et blanc
- dessin au trait
- lignes propres et nettes
- détails suffisamment riches pour être intéressants
- détails adaptés à {AGE} ans : formes larges et simples pour les plus jeunes,
  détails modérés pour les plus grands, jamais de petites zones surchargées
- espaces suffisamment grands pour être facilement coloriés
- composition verticale
- personnage principal clairement visible
- décor détaillé mais facile à colorier
- style professionnel de livre pour enfants
- aucun remplissage de couleur
- fond blanc pur, aucun aplat gris, aucune ombre, aucun dégradé, aucune hachure
- cheveux et vêtements non remplis, seulement leurs contours à colorier
- composition ouverte en vignette : tous les éléments restent à distance des bords
- aucun cadre rectangulaire, aucune bordure, aucun élément coupé sur le pourtour
- limiter les ornements à quelques motifs discrets de l'univers du récit
- aucun effet photographique
- aucun réalisme photographique

RÈGLES IMPORTANTES
- aucun texte dans l'image
- aucune lettre
- aucun titre
- aucun logo
- aucune bulle de dialogue
- aucun watermark
- aucun personnage provenant d'une œuvre existante
- ne pas utiliser de personnage sous copyright
- conserver l'apparence de l'enfant
- conserver l'apparence des personnages récurrents
- respecter les actions, objets et décors décrits dans la scène
- ne pas transformer une scène de l'histoire en couverture

L'image doit être prête à être utilisée comme page
d'un véritable livre de coloriage pour enfants.
"""

        result = client.images.edit(
            model="gpt-image-2",
            image=[reference_image],
            prompt=prompt,
            size="1024x1536",
            quality="medium"
        )

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        atomic_write_bytes(filename, image_bytes)

        print(f"✅ Page {page_number} créée : {filename}")

    finally:
        if reference_image is not None:
            reference_image.close()


def generate_all_pages(progress=None):
    print("\n" + "=" * 60)
    print("🎨 ÉTAPE 3/5 — GÉNÉRATION DES ILLUSTRATIONS")
    print("=" * 60)

    story = Path(STORY_FILE).read_text(encoding="utf-8")

    for page_number in range(1, NUMBER_OF_PAGES + 1):
        page_content = get_page(story, page_number)

        if page_content is None:
            raise ValueError(f"PAGE {page_number} introuvable dans l'histoire.")

        if progress:
            progress("illustrations", f"Illustration {page_number}/{NUMBER_OF_PAGES} en cours", page_index=page_number-1, page_total=NUMBER_OF_PAGES)
        generate_page(page_number, page_content)
        if progress:
            progress("illustrations", f"Illustration {page_number}/{NUMBER_OF_PAGES} terminée", page_index=page_number, page_total=NUMBER_OF_PAGES)

    print("\n✅ Les illustrations sont prêtes.")


# ============================================================
# 3. GÉNÉRATION DE LA COUVERTURE
# ============================================================

def generate_cover():
    global BOOK_TITLE

    print("\n" + "=" * 60)
    print("📕 ÉTAPE 4/5 — GÉNÉRATION DE LA COUVERTURE")
    print("=" * 60)

    if REUSE_EXISTING_FILES and Path(COVER_FILE).exists():
        print(f"⏭️ Couverture déjà existante : {COVER_FILE}")
        return

    BOOK_TITLE = get_book_title()
    print(f"📚 Titre du livre : {BOOK_TITLE}")

    require_file(
        REFERENCE_IMAGE,
        f"❌ Image de référence introuvable : {REFERENCE_IMAGE}"
    )

    reference_image = open(REFERENCE_IMAGE, "rb")

    try:
        prompt = f"""
{gender_instruction(CHILD_GENDER)}
Crée une couverture de livre pour enfants en couleur.

Utilise l'image fournie comme référence principale pour le personnage.

Le personnage doit rester reconnaissable :
- même visage général
- même coiffure
- même apparence générale
- même âge apparent

Le personnage principal est l'enfant du livre.

THÈME :
{THEME}

Crée une scène de couverture spectaculaire mais adaptée
aux enfants, directement inspirée du thème.

STYLE :
- illustration professionnelle pour livre jeunesse
- très colorée
- joyeuse
- aventureuse
- haute qualité
- composition verticale
- personnage au premier plan
- univers cohérent avec le thème

La couverture doit contenir exactement ces textes :

{BOOK_TITLE}

{NAME}

Livre de coloriage personnalisé

IMPORTANT :
Le titre principal doit être exactement « {BOOK_TITLE} ».
Ne pas écrire « Une aventure de {NAME} » et ne pas inventer un autre titre.

Les textes doivent être grands, lisibles et bien intégrés
dans le design.

Ne pas utiliser de personnage ou d'univers provenant
d'une œuvre existante.
"""

        result = client.images.edit(
            model="gpt-image-2",
            image=[reference_image],
            prompt=prompt,
            size="1024x1536",
            quality="medium"
        )

        image_base64 = result.data[0].b64_json
        atomic_write_bytes(COVER_FILE,
            base64.b64decode(image_base64)
        )

        print(f"✅ Couverture créée : {COVER_FILE}")

    finally:
        reference_image.close()


# ============================================================
# 4. GÉNÉRATION DU PDF
# ============================================================

def get_pdf_page(story, page_number):
    pattern = rf"PAGE\s+{page_number}(.*?)(?=PAGE\s+{page_number + 1}|$)"
    match = re.search(
        pattern, story, re.IGNORECASE | re.DOTALL
    )
    return match.group(1).strip() if match else ""


def clean_page_content(content):
    title_match = re.search(
        r"(?ims)^\s*Titre\s*:\s*(.*?)(?=^\s*Texte\s*:|^\s*Scène à illustrer\s*:|$)",
        content
    )

    text_match = re.search(
        r"(?ims)^\s*Texte\s*:\s*(.*?)(?=^\s*Scène à illustrer\s*:|$)",
        content
    )

    title = title_match.group(1).strip() if title_match else ""
    text = text_match.group(1).strip() if text_match else ""

    text = re.sub(r"\s*\n\s*", " ", text)

    return title, text


def fit_image_to_box(image_path, max_width, max_height):
    reader = ImageReader(image_path)
    original_width, original_height = reader.getSize()

    scale = min(
        max_width / original_width,
        max_height / original_height
    )

    image = Image(
        image_path,
        width=original_width * scale,
        height=original_height * scale
    )

    image.hAlign = "CENTER"
    return image


def generate_keepsake_medallion():
    if REUSE_EXISTING_FILES and Path(KEEPSAKE_IMAGE).exists():
        return
    pages = story_pages(Path(STORY_FILE).read_text(encoding="utf-8"), NUMBER_OF_PAGES)
    with open(REFERENCE_IMAGE, "rb") as reference:
        result = client.images.edit(
            model="gpt-image-2", image=[reference], size="1024x1024", quality="medium",
            prompt=f"""Crée uniquement le médaillon souvenir à colorier de {NAME}, {AGE} ans.
{gender_instruction(CHILD_GENDER)}
Conserve exactement le personnage de référence : visage, coiffure, âge, apparence.
Univers : {THEME}. Mission accomplie : {pages[-1]["scene"]}.
Personnage principal fier et souriant, au centre, buste ou corps en entier dans
un médaillon circulaire très simple. Ajouter le compagnon uniquement si la scène
le mentionne et si cela reste lisible. Tous les traits restent dans le cercle.
Médaillon entier visible et généreuse marge blanche tout autour.
Noir et blanc pur, contours nets, larges zones à colorier adaptées à {AGE} ans,
fond blanc, aucun gris, aucune ombre, hachure, texture ou aplat noir.
AUCUN TEXTE, lettre, numéro, titre, ruban, logo ou watermark.
Les inscriptions et le ruban seront ajoutés par le système PDF.""")
    atomic_write_bytes(KEEPSAKE_IMAGE, base64.b64decode(result.data[0].b64_json))


def generate_pdf():
    story = Path(STORY_FILE).read_text(encoding="utf-8")
    pages = story_pages(story, NUMBER_OF_PAGES)
    for page in pages:
        page["image"] = PAGES_FOLDER / f"page_{page["number"]:02d}.png"
    return build_book_pdf(OUTPUT_FILE, pages, KEEPSAKE_IMAGE, child_name=NAME,
        congratulations=keepsake_congratulations(story, THEME, LANGUAGE),
        gender=CHILD_GENDER, language=LANGUAGE, cover=COVER_FILE)



def main():
    print("\n" + "#" * 60)
    print("       📚 GÉNÉRATEUR DE LIVRE PERSONNALISÉ")
    print("#" * 60)

    print(f"\n👤 Enfant : {NAME}")
    print(f"🎂 Âge : {AGE} ans")
    print(f"🎨 Thème : {THEME}")
    print(f"🌍 Langue : {LANGUAGE}")

    reuse_existing_book = prepare_project()

    if reuse_existing_book:
        print("⏭️ Fichiers déjà validés : réutilisation.")
        print("   Seul le PDF sera reconstruit.")
    else:
        generate_character_reference()
        generate_story()
        BOOK_TITLE = get_book_title()
        print(f"📚 Titre généré : {BOOK_TITLE}")
        generate_all_pages()
        generate_cover()

    generate_keepsake_medallion()
    generate_pdf()

    print("\n🎉 PROCESSUS TERMINÉ !")
    print(f"📕 Livre final : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
