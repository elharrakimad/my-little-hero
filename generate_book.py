from openai import OpenAI
import base64
import hashlib
import html
import re
from pathlib import Path
from child_profile import gender_instruction

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
Le texte de chaque page doit contenir environ 2 à 4 phrases.
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
- espaces suffisamment grands pour être facilement coloriés
- composition verticale
- personnage principal clairement visible
- décor détaillé mais facile à colorier
- style professionnel de livre pour enfants
- aucun remplissage de couleur
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


def generate_all_pages():
    print("\n" + "=" * 60)
    print("🎨 ÉTAPE 3/5 — GÉNÉRATION DES ILLUSTRATIONS")
    print("=" * 60)

    story = Path(STORY_FILE).read_text(encoding="utf-8")

    for page_number in range(1, NUMBER_OF_PAGES + 1):
        page_content = get_page(story, page_number)

        if page_content is None:
            print(f"❌ PAGE {page_number} introuvable dans story.txt")
            continue

        generate_page(page_number, page_content)

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


def generate_pdf():
    print("\n" + "=" * 60)
    print("📄 ÉTAPE 5/5 — GÉNÉRATION DU PDF")
    print("=" * 60)

    require_file(COVER_FILE, "❌ cover.png est introuvable.")
    require_file(STORY_FILE, "❌ story.txt est introuvable.")

    if not PAGES_FOLDER.is_dir():
        raise FileNotFoundError("❌ Le dossier 'pages' est introuvable.")

    story = Path(STORY_FILE).read_text(encoding="utf-8")

    styles = getSampleStyleSheet()

    page_title_style = ParagraphStyle(
        "PageTitle",
        parent=styles["Heading2"],
        alignment=TA_CENTER,
        fontSize=17,
        leading=20,
        spaceBefore=0,
        spaceAfter=0,
        textColor="#202020",
    )

    text_style = ParagraphStyle(
        "StoryText",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        fontSize=10.5,
        leading=14,
        leftIndent=0.5 * cm,
        rightIndent=0.5 * cm,
        spaceAfter=3,
    )

    coloring_style = ParagraphStyle(
        "Coloring",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=12,
        spaceBefore=2,
    )

    final_title_style = ParagraphStyle(
        "FinalTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=28,
        leading=34,
        spaceAfter=20,
    )

    PAGE_WIDTH, PAGE_HEIGHT = A4
    MARGIN = 0.7 * cm
    AVAILABLE_WIDTH = PAGE_WIDTH - (2 * MARGIN)

    def draw_cover(canvas, doc):
        reader = ImageReader(COVER_FILE)
        original_width, original_height = reader.getSize()

        scale = min(
            PAGE_WIDTH / original_width,
            PAGE_HEIGHT / original_height
        )

        width = original_width * scale
        height = original_height * scale
        x = (PAGE_WIDTH - width) / 2
        y = (PAGE_HEIGHT - height) / 2

        canvas.drawImage(
            reader,
            x,
            y,
            width=width,
            height=height,
            preserveAspectRatio=True,
            mask="auto"
        )

    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN
    )

    pdf = []

    # Première page : couverture dessinée directement
    pdf.append(PageBreak())

    for page_number in range(1, NUMBER_OF_PAGES + 1):
        print(f"📖 Création de la page PDF {page_number}...")

        content = get_pdf_page(story, page_number)
        title, text = clean_page_content(content)

        image_path = PAGES_FOLDER / f"page_{page_number:02d}.png"

        require_file(
            image_path,
            f"❌ Image manquante : {image_path}"
        )

        pdf.append(Spacer(1, 0.15 * cm))

        pdf.append(
            HRFlowable(
                width="32%",
                thickness=1,
                color="#555555",
                spaceBefore=0,
                spaceAfter=0.08 * cm,
                hAlign="CENTER"
            )
        )

        ornament_style = ParagraphStyle(
            "Ornament",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            fontSize=8,
            leading=9,
            spaceBefore=0,
            spaceAfter=0.05 * cm
        )

        pdf.append(Paragraph("◆", ornament_style))

        if title:
            pdf.append(Paragraph(
                html.escape(title),
                page_title_style
            ))

        pdf.append(
            HRFlowable(
                width="22%",
                thickness=0.8,
                color="#777777",
                spaceBefore=0.12 * cm,
                spaceAfter=0
            )
        )

        pdf.append(Spacer(1, 0.38 * cm))

        image = fit_image_to_box(
            image_path,
            AVAILABLE_WIDTH,
            21.5 * cm
        )

        pdf.append(image)
        pdf.append(Spacer(1, 0.22 * cm))

        if text:
            story_text = Paragraph(
                html.escape(text),
                text_style
            )

            story_box = Table(
                [[story_text]],
                colWidths=[AVAILABLE_WIDTH - 1.0 * cm]
            )

            story_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1),
                 colors.HexColor("#F7F7F7")),
                ("BOX", (0, 0), (-1, -1),
                 0.8, colors.HexColor("#B8B8B8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 0.35 * cm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0.35 * cm),
                ("TOPPADDING", (0, 0), (-1, -1), 0.18 * cm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.18 * cm),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))

            pdf.append(story_box)
            pdf.append(Spacer(1, 0.10 * cm))

        coloring_message = {
            "français": "À toi de colorier !",
            "english": "Time to color!",
            "español": "¡A colorear!"
        }.get(LANGUAGE.lower(), "À toi de colorier !")

        pdf.append(
            Paragraph(
                coloring_message,
                coloring_style
            )
        )

        pdf.append(
            Paragraph(
                f"— {page_number} —",
                coloring_style
            )
        )

        pdf.append(PageBreak())

    final_message = {
        "français": (
            f"Ton aventure est terminée...<br/><br/>"
            f"Mais de nouvelles aventures commencent "
            f"toujours avec un peu d'imagination !"
        ),
        "english": (
            f"Your adventure is over...<br/><br/>"
            f"But new adventures always begin "
            f"with a little imagination!"
        ),
        "español": (
            f"Tu aventura ha terminado...<br/><br/>"
            f"¡Pero nuevas aventuras siempre comienzan "
            f"con un poco de imaginación!"
        )
    }.get(
        LANGUAGE.lower(),
        "Ton aventure est terminée..."
    )

    bravo = {
        "français": f"Bravo, {NAME} !",
        "english": f"Well done, {NAME}!",
        "español": f"¡Bravo, {NAME}!"
    }.get(LANGUAGE.lower(), f"Bravo, {NAME} !")

    pdf.append(Spacer(1, 5 * cm))
    pdf.append(Paragraph(
        html.escape(bravo),
        final_title_style
    ))
    pdf.append(Paragraph(
        final_message,
        text_style
    ))

    print("📕 Construction du PDF A4...")

    doc.build(
        pdf,
        onFirstPage=draw_cover
    )

    print("\n" + "=" * 60)
    print("✅ LIVRE COMPLET CRÉÉ !")
    print("=" * 60)
    print(f"📕 {OUTPUT_FILE}")
    print("👤 Personnage : OK")
    print("📖 Histoire : OK")
    print("🎨 Illustrations : OK")
    print("🖼️ Couverture : OK")
    print("📄 PDF A4 : OK")
    print("=" * 60)


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

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

    generate_pdf()

    print("\n🎉 PROCESSUS TERMINÉ !")
    print(f"📕 Livre final : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
