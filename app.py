import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import urllib.parse
import base64
import json
import uuid
import io
from datetime import datetime
from openai import OpenAI
from supabase import create_client

# ============================================================
# MY LITTLE HERO — V3
# Parcours commercial en 4 étapes
# 1. Offre → 2. Héros → 3. Aventures → 4. Aperçu & commande
# ============================================================

st.set_page_config(
    page_title="My Little Hero",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
ASSETS = Path("assets")
LOGO = ASSETS / "logo.png"

# Remplace par ton numéro WhatsApp au format international.
# Exemple Maroc : 2126XXXXXXXX
WHATSAPP_NUMBER = "212XXXXXXXXX"

SUPABASE_BUCKET = "my-little-hero-files"


def get_supabase_client():
    """Create the server-side Supabase client from Streamlit Secrets."""
    url = st.secrets.get("SUPABASE_URL", "").strip()
    key = (
        st.secrets.get("SUPABASE_SECRET_KEY", "")
        or st.secrets.get("SUPABASE_SERVICE_KEY", "")
    ).strip()

    if not url or not key:
        raise RuntimeError(
            "Supabase n'est pas configuré. Ajoute SUPABASE_URL et "
            "SUPABASE_SECRET_KEY dans les Secrets Streamlit."
        )

    return create_client(url, key)


def upload_private_file(supabase, storage_path, data, content_type):
    """Upload a file into the private My Little Hero bucket."""
    supabase.storage.from_(SUPABASE_BUCKET).upload(
        storage_path,
        data,
        file_options={
            "content-type": content_type,
            "upsert": "true",
        },
    )
    return storage_path


def get_order_number():
    if not st.session_state.get("order_number"):
        st.session_state.order_number = (
            f"MLH-{datetime.now().strftime('%Y%m%d')}-"
            f"{(st.session_state.preview_id or uuid.uuid4().hex)[-6:].upper()}"
        )
    return st.session_state.order_number

PRICES = {
    1: {"digital": 69, "print": 99, "both": 129},
    2: {"digital": 119, "print": 179, "both": 219},
    3: {"digital": 159, "print": 249, "both": 299},
}

FORMAT_NAMES = {
    "digital": "💻 Digital",
    "print": "📚 Imprimé",
    "both": "🎁 Digital + Imprimé",
}

THEMES = [
    "🎮 Monde de jeu vidéo",
    "🚀 Voyage dans l'espace",
    "🐉 Chevalier et dragon",
    "🦸 Super héros",
    "🏴‍☠️ Aventure de pirates",
    "🧙 Monde magique",
    "🦖 Aventure avec les dinosaures",
    "⚽ Aventure football",
    "🏎️ Course et vitesse",
    "🌊 Aventure sous-marine",
    "🌳 Forêt mystérieuse",
    "✨ Mon propre thème",
]

LANGUAGES = ["Français", "English", "Español"]

PACK_NAMES = {
    1: "LITTLE HERO",
    2: "SUPER HERO",
    3: "HERO GIFT",
}

PACK_ICONS = {
    1: "🌟",
    2: "⭐",
    3: "👑",
}


# ------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------
if "step" not in st.session_state:
    st.session_state.step = 1

if "pack" not in st.session_state:
    st.session_state.pack = 1

if "format" not in st.session_state:
    st.session_state.format = "digital"

if "child_name" not in st.session_state:
    st.session_state.child_name = ""

if "customer_phone" not in st.session_state:
    st.session_state.customer_phone = ""

if "customer_email" not in st.session_state:
    st.session_state.customer_email = ""

if "age" not in st.session_state:
    st.session_state.age = 8

if "language" not in st.session_state:
    st.session_state.language = "Français"

if "photo" not in st.session_state:
    st.session_state.photo = None

if "adventures" not in st.session_state:
    st.session_state.adventures = []

if "preview_id" not in st.session_state:
    st.session_state.preview_id = None

if "order_number" not in st.session_state:
    st.session_state.order_number = None
if "reference_path" not in st.session_state:
    st.session_state.reference_path = None
if "cover_paths" not in st.session_state:
    st.session_state.cover_paths = []

# ------------------------------------------------------------
# IA — GENERATION DES COUVERTURES UNIQUEMENT
# ------------------------------------------------------------
def _image_file(data: bytes, filename: str):
    """Create a named in-memory image so the OpenAI SDK sends the correct MIME type."""
    file_obj = io.BytesIO(data)
    file_obj.name = filename
    file_obj.seek(0)
    return file_obj


def generate_character_reference(photo_bytes, name, age, photo_filename="enfant.jpg"):
    client = OpenAI()
    # Streamlit's UploadedFile/BytesIO can otherwise be sent as application/octet-stream.
    # Giving the in-memory file an image filename lets the SDK infer image/jpeg or image/png.
    result = client.images.edit(
        model="gpt-image-2",
        image=[_image_file(photo_bytes, photo_filename)],
        prompt=f"""
Crée une référence visuelle cohérente du personnage principal d'un livre jeunesse personnalisé.
Utilise la photo fournie uniquement comme référence visuelle de l'enfant.
L'enfant s'appelle {name} et a {age} ans.

IMPORTANT : conserver les traits généraux du visage, la coiffure,
l'apparence générale reconnaissable et l'âge apparent.
Créer un personnage original, avec une tenue simple et neutre,
sans thème particulier. Illustration jeunesse professionnelle,
composition verticale, personnage visible en entier, arrière-plan simple.
Aucun texte, logo ou watermark. Aucun personnage ou univers protégé.
Cette image servira de référence commune pour toutes les aventures du pack.
""",
        size="1024x1536",
        quality="medium",
    )
    return base64.b64decode(result.data[0].b64_json)


def generate_adventure_title(name, age, theme, idea, quality, language):
    """Generate one original title for one adventure."""
    client = OpenAI()

    language_instruction = {
        "Français": "Écris le titre en français.",
        "English": "Write the title in English.",
        "Español": "Escribe el título en español.",
    }.get(language, "Écris le titre dans la langue demandée.")

    prompt = f"""
Tu es le directeur éditorial de My Little Hero, une marque de livres
personnalisés pour enfants.

Invente UN SEUL titre de livre original pour cette aventure.

ENFANT : {name}, {age} ans
THÈME : {theme}
IDÉE DU CLIENT : {idea if idea else "Aucune idée supplémentaire."}
QUALITÉ À METTRE EN VALEUR : {quality if quality else "Aucune demande particulière."}

{language_instruction}

Le titre doit :
- être court, mémorable et adapté à un livre jeunesse ;
- être directement inspiré du thème et de l'aventure ;
- être différent de "L'aventure de {name}" ;
- donner envie de découvrir l'histoire ;
- être original ;
- ne contenir aucun personnage, marque, film, série, jeu vidéo ou univers protégé ;
- ne contenir ni guillemets, ni emoji, ni sous-titre.

Réponds uniquement avec le titre final, sur une seule ligne.
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt
    )

    title = response.output_text.strip().replace("\n", " ")
    title = title.strip('"“”')

    if not title:
        raise ValueError("L'IA n'a pas généré de titre.")

    return title[:120]


def generate_cover(reference_bytes, name, age, theme, idea, quality, language, book_title):
    client = OpenAI()
    if language == "English":
        subtitle_text = "Personalized Coloring Book"
    elif language == "Español":
        subtitle_text = "Libro de colorear personalizado"
    else:
        subtitle_text = "Livre de coloriage personnalisé"

    title_text = book_title

    result = client.images.edit(
        model="gpt-image-2",
        image=[_image_file(reference_bytes, "character_reference.png")],
        prompt=f"""
Crée la couverture couleur professionnelle d'un livre jeunesse personnalisé.
Utilise l'image fournie comme référence principale du personnage.
Le personnage doit rester reconnaissable : même visage général,
même coiffure, même âge apparent et même apparence générale.

PERSONNAGE : {name}, {age} ans
THÈME : {theme}
IDÉE DU CLIENT : {idea if idea else 'Aucune idée supplémentaire.'}
QUALITÉ : {quality if quality else 'Aucune demande particulière.'}

Crée une scène de couverture joyeuse, magique et aventureuse,
avec l'enfant clairement au premier plan et un décor riche inspiré du thème.

STYLE : illustration professionnelle de livre jeunesse, très colorée,
chaleureuse, joyeuse, composition verticale, rendu premium.
Personnages et univers totalement originaux. Aucun personnage existant,
aucun logo de marque, aucun watermark.

AFFICHER EXACTEMENT CES TEXTES :
"{title_text}"
"{subtitle_text}"
Les textes doivent être grands, lisibles et bien intégrés.
Ne pas ajouter d'autres textes.
""",
        size="1024x1536",
        quality="medium",
    )
    return base64.b64decode(result.data[0].b64_json)


def save_order_metadata():
    """Save the order in Supabase and keep a local copy for compatibility."""
    if not st.session_state.preview_id:
        raise ValueError("Aucun aperçu n'est disponible pour cette commande.")

    if not st.session_state.reference_path:
        raise ValueError("La référence du personnage est introuvable.")

    supabase = get_supabase_client()
    preview_dir = Path("orders") / f"preview_{st.session_state.preview_id}"
    preview_dir.mkdir(parents=True, exist_ok=True)

    selected_adventures = list(st.session_state.adventures[:st.session_state.pack])
    order_number = get_order_number()
    storage_root = f"orders/{order_number}"

    # Upload the reference and covers to the private Supabase bucket.
    reference_local = Path(st.session_state.reference_path)
    reference_storage_path = f"{storage_root}/reference/character_reference.png"
    upload_private_file(
        supabase,
        reference_storage_path,
        reference_local.read_bytes(),
        "image/png",
    )

    remote_cover_paths = []
    for i, cover_path in enumerate(st.session_state.cover_paths, start=1):
        cover_storage_path = f"{storage_root}/covers/cover_{i:02d}.png"
        upload_private_file(
            supabase,
            cover_storage_path,
            Path(cover_path).read_bytes(),
            "image/png",
        )
        remote_cover_paths.append(cover_storage_path)

    order = {
        "preview_id": st.session_state.preview_id,
        "order_number": order_number,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "WAITING_FOR_PAYMENT",
        "child_name": st.session_state.child_name,
        "customer_phone": st.session_state.customer_phone,
        "customer_email": st.session_state.customer_email,
        "age": st.session_state.age,
        "language": st.session_state.language,
        "pack": st.session_state.pack,
        "format": st.session_state.format,
        "price": PRICES[st.session_state.pack][st.session_state.format],
        "reference_path": reference_storage_path,
        "adventures": [],
    }

    for i, adventure in enumerate(selected_adventures, start=1):
        theme = (
            adventure["custom"]
            if adventure["theme"] == "✨ Mon propre thème"
            else adventure["theme"]
        )
        order["adventures"].append({
            "number": i,
            "theme": theme,
            "idea": adventure["idea"],
            "quality": adventure["quality"],
            "title": adventure.get("title", ""),
        })

    order["cover_paths"] = remote_cover_paths

    # Supabase is now the source of truth for online orders.
    row = {
        "order_ref": order_number,
        "parent_name": None,
        "parent_phone": st.session_state.customer_phone,
        "parent_email": st.session_state.customer_email,
        "child_name": st.session_state.child_name,
        "child_age": st.session_state.age,
        "language": st.session_state.language,
        "pack": PACK_NAMES[st.session_state.pack],
        "adventure_count": st.session_state.pack,
        "total_price": PRICES[st.session_state.pack][st.session_state.format],
        "status": "WAITING_FOR_PAYMENT",
        "adventures": order["adventures"],
        "reference_path": reference_storage_path,
        "cover_paths": remote_cover_paths,
        "generated_files": [],
    }

    existing = (
        supabase.table("orders")
        .select("id")
        .eq("order_ref", order_number)
        .limit(1)
        .execute()
    )

    if existing.data:
        supabase.table("orders").update(row).eq("order_ref", order_number).execute()
    else:
        supabase.table("orders").insert(row).execute()

    # Keep a local JSON copy only as a temporary compatibility layer.
    (preview_dir / "order.json").write_text(
        json.dumps(order, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return preview_dir / "order.json"


def create_preview_covers():
    if not st.session_state.photo:
        raise ValueError("Photo manquante.")

    # Verify the shared backend before spending AI credits.
    get_supabase_client()

    preview_id = st.session_state.preview_id or uuid.uuid4().hex[:12]
    preview_dir = Path("orders") / f"preview_{preview_id}"
    preview_dir.mkdir(parents=True, exist_ok=True)

    photo_bytes = st.session_state.photo.getvalue()
    (preview_dir / "child_photo.jpg").write_bytes(photo_bytes)
    reference_path = preview_dir / "character_reference.png"

    if reference_path.exists():
        reference_bytes = reference_path.read_bytes()
    else:
        with st.status("✨ Ton héros prend vie...", expanded=False):
            reference_bytes = generate_character_reference(
                photo_bytes,
                st.session_state.child_name,
                st.session_state.age,
                getattr(st.session_state.photo, "name", "enfant.jpg"),
            )
        reference_path.write_bytes(reference_bytes)

    # IMPORTANT : le nombre de couvertures doit toujours être égal au nombre
    # d'aventures sélectionnées.
    selected_adventures = list(st.session_state.adventures[:st.session_state.pack])
    cover_paths = []
    total = len(selected_adventures)

    for i, adventure in enumerate(selected_adventures, start=1):
        cover_path = preview_dir / f"cover_{i:02d}.png"
        theme = adventure["custom"] if adventure["theme"] == "✨ Mon propre thème" else adventure["theme"]

        # Chaque aventure reçoit son propre titre IA.
        if not adventure.get("title"):
            with st.status(f"✨ Création du titre de l'aventure {i}/{total}...", expanded=False):
                adventure["title"] = generate_adventure_title(
                    st.session_state.child_name,
                    st.session_state.age,
                    theme,
                    adventure["idea"],
                    adventure["quality"],
                    st.session_state.language,
                )

        if not cover_path.exists():
            with st.status(f"🎨 Création de la couverture {i}/{total}...", expanded=False):
                cover_bytes = generate_cover(
                    reference_bytes,
                    st.session_state.child_name,
                    st.session_state.age,
                    theme,
                    adventure["idea"],
                    adventure["quality"],
                    st.session_state.language,
                    adventure["title"],
                )
            cover_path.write_bytes(cover_bytes)

        cover_paths.append(str(cover_path))

    st.session_state.preview_id=preview_id
    st.session_state.reference_path=str(reference_path)
    st.session_state.cover_paths=cover_paths

# ------------------------------------------------------------
# STYLE
# ------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Poppins:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

.stApp {
    background: linear-gradient(180deg, #fffaf5 0%, #ffffff 52%, #f7fbff 100%);
}

.block-container {
    max-width: 1160px;
    padding-top: 1.1rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    font-family: 'Baloo 2', sans-serif !important;
}

.hero {
    text-align: center;
    padding: .4rem 1rem 1.4rem;
}

.hero-title {
    font-family: 'Baloo 2', sans-serif;
    font-size: 3.5rem;
    line-height: 1;
    font-weight: 800;
    background: linear-gradient(90deg, #ff6b6b, #ffb84d, #6c63ff, #43c6ac);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-size: 1.25rem;
    font-weight: 600;
    color: #34344a;
    margin-top: .6rem;
}

.hero-text {
    max-width: 720px;
    margin: .4rem auto 0;
    color: #707070;
}

.steps {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin: .5rem 0 2rem;
    flex-wrap: wrap;
}

.step {
    padding: 8px 15px;
    border-radius: 30px;
    background: #eeeeee;
    color: #777;
    font-size: .85rem;
    font-weight: 600;
}

.step.active {
    background: #303047;
    color: white;
}

.step.done {
    background: #e9f8ef;
    color: #24834b;
}

.section-title {
    text-align: center;
    font-family: 'Baloo 2', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    color: #303047;
    margin: 1rem 0 .5rem;
}

.section-text {
    text-align: center;
    color: #777;
    margin-bottom: 1.2rem;
}

.offer-card {
    background: white;
    border: 2px solid #ededed;
    border-radius: 24px;
    padding: 1.35rem;
    text-align: center;
    box-shadow: 0 8px 28px rgba(40,40,80,.07);
    min-height: 300px;
}

.offer-card.selected {
    border-color: #6c63ff;
    box-shadow: 0 10px 30px rgba(108,99,255,.16);
}

.offer-card.popular {
    border-color: #ffd166;
}

.offer-name {
    font-family: 'Baloo 2', sans-serif;
    font-size: 1.7rem;
    font-weight: 800;
    color: #303047;
}

.offer-desc {
    color: #777;
    min-height: 48px;
    font-size: .9rem;
}

.offer-price {
    font-size: 1rem;
    padding: 4px;
    color: #444;
}

.offer-price strong {
    font-size: 1.1rem;
    color: #24243a;
}

.format-box {
    background: white;
    border: 1px solid #ececf4;
    border-radius: 20px;
    padding: 1rem 1.3rem;
    margin-top: 1rem;
    box-shadow: 0 5px 18px rgba(30,30,60,.04);
}

.summary {
    background: linear-gradient(135deg, #fff7e8, #f5f4ff);
    border: 2px solid #eee7d6;
    border-radius: 22px;
    padding: 1.3rem;
    margin-top: 1rem;
}

.total {
    text-align: center;
    font-family: 'Baloo 2', sans-serif;
    font-size: 2.3rem;
    font-weight: 800;
    color: #303047;
    margin-top: .4rem;
}

.cover-zone {
    background: white;
    border-radius: 28px;
    padding: 1.5rem;
    box-shadow: 0 10px 35px rgba(40,40,80,.08);
    border: 1px solid #eee;
    text-align: center;
}

.book-row {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    gap: 52px;
    flex-wrap: wrap;
    margin: 2.5rem 0 1.5rem;
    padding: 30px 15px 42px;
}

.book-wrap {
    position: relative;
    width: 285px;
    text-align: center;
    perspective: 1400px;
}

.book-number {
    display: inline-block;
    position: relative;
    z-index: 20;
    background: rgba(255,255,255,.96);
    padding: 7px 15px;
    border-radius: 999px;
    color: #38384d;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: .2px;
    box-shadow: 0 7px 22px rgba(34,34,65,.12);
    margin-bottom: 14px;
}

.book-3d {
    position: relative;
    width: 225px;
    height: 330px;
    margin: 0 auto;
    transform-style: preserve-3d;
    transform: rotateY(-17deg) rotateX(3deg) rotateZ(-1deg);
    transition: transform .35s ease, filter .35s ease;
    filter:
        drop-shadow(18px 25px 17px rgba(35,35,60,.22))
        drop-shadow(2px 4px 5px rgba(35,35,60,.12));
}

.book-wrap:hover .book-3d {
    transform: rotateY(-9deg) rotateX(1deg) rotateZ(0deg) translateY(-6px);
    filter:
        drop-shadow(21px 28px 20px rgba(35,35,60,.25))
        drop-shadow(2px 5px 7px rgba(35,35,60,.12));
}

.book-cover-image {
    position: absolute;
    left: 13px;
    top: 0;
    width: 212px;
    height: 330px;
    object-fit: cover;
    object-position: center;
    display: block;
    border-radius: 2px 12px 12px 2px;
    z-index: 8;
    border: 1px solid rgba(20,20,30,.18);
    box-shadow:
        inset -7px 0 0 rgba(255,255,255,.12),
        inset 4px 0 0 rgba(0,0,0,.13),
        0 0 0 1px rgba(255,255,255,.25);
    backface-visibility: hidden;
}

.book-spine {
    position: absolute;
    left: 0;
    top: 1px;
    width: 17px;
    height: 328px;
    z-index: 10;
    border-radius: 5px 0 0 5px;
    background:
        linear-gradient(
            90deg,
            rgba(15,15,20,.72) 0%,
            rgba(255,255,255,.22) 18%,
            rgba(20,20,30,.30) 48%,
            rgba(255,255,255,.18) 72%,
            rgba(10,10,15,.55) 100%
        );
    box-shadow:
        inset -1px 0 rgba(255,255,255,.32),
        inset 2px 0 rgba(0,0,0,.24);
}

.book-pages {
    position: absolute;
    right: -13px;
    top: 7px;
    width: 17px;
    height: 316px;
    z-index: 2;
    border-radius: 0 5px 5px 0;
    background:
        repeating-linear-gradient(
            to bottom,
            #fffef9 0px,
            #fffef9 3px,
            #e5e2da 4px,
            #fffef9 6px
        );
    box-shadow:
        3px 5px 8px rgba(0,0,0,.22),
        inset 1px 0 rgba(0,0,0,.08);
    transform: skewY(-1deg);
}

.book-top-edge {
    position: absolute;
    left: 13px;
    top: -5px;
    width: 212px;
    height: 7px;
    z-index: 7;
    border-radius: 8px 12px 0 0;
    background: linear-gradient(180deg, rgba(255,255,255,.55), rgba(0,0,0,.10));
}

.book-bottom-edge {
    position: absolute;
    left: 13px;
    bottom: -5px;
    width: 212px;
    height: 8px;
    z-index: 7;
    border-radius: 0 0 12px 8px;
    background: linear-gradient(180deg, rgba(0,0,0,.16), rgba(255,255,255,.28));
}

.book-gold-line {
    position: absolute;
    left: 18px;
    top: 5px;
    width: 202px;
    height: 2px;
    z-index: 12;
    background: linear-gradient(90deg, transparent, rgba(255,215,130,.75), transparent);
    opacity: .7;
}

.book-bottom-shadow {
    width: 235px;
    height: 32px;
    margin: 0 auto -2px;
    background: radial-gradient(ellipse, rgba(24,24,40,.30), rgba(24,24,40,.08) 45%, transparent 72%);
    filter: blur(5px);
}

.book-caption {
    margin-top: 10px;
    color: #666;
    font-size: 12px;
    font-weight: 600;
}

.lock-box {
    background: linear-gradient(135deg,#f7f4ff,#fff7e8);
    border: 2px solid #e8e1f8;
    border-radius: 24px;
    padding: 1.3rem;
    text-align: center;
    margin-top: 1.4rem;
}

.lock-title {
    font-family: 'Baloo 2';
    font-size: 1.7rem;
    font-weight: 800;
    color: #303047;
}

.lock-text {
    color: #666;
}

.footer {
    text-align: center;
    color: #888;
    padding: 2rem;
}

div.stButton > button {
    border-radius: 14px;
    font-weight: 700;
    min-height: 46px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
if LOGO.exists():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image(str(LOGO), use_container_width=True)

st.markdown("""
<div class="hero">
    <div class="hero-title">MY LITTLE HERO</div>
    <div class="hero-subtitle">Chaque enfant devient le héros de sa propre histoire.</div>
    <div class="hero-text">
        Une aventure personnalisée à partir de la photo de ton enfant,
        créée pour lire, imaginer et colorier.
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# INDICATEUR DES 4 ÉTAPES
# ------------------------------------------------------------
step_labels = ["1. Offre", "2. Mon héros", "3. Mes aventures", "4. Aperçu & commande"]
step_html = '<div class="steps">'

for i, label in enumerate(step_labels, start=1):
    cls = "active" if i == st.session_state.step else ("done" if i < st.session_state.step else "")
    step_html += f'<div class="step {cls}">{label}</div>'

step_html += "</div>"
st.markdown(step_html, unsafe_allow_html=True)

# ============================================================
# ETAPE 1 — OFFRE
# ============================================================
if st.session_state.step == 1:

    st.markdown('<div class="section-title">✨ Choisis ton pack</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-text">Le même petit héros peut vivre plusieurs aventures.</div>',
        unsafe_allow_html=True
    )

    cols = st.columns(3)

    descriptions = {
        1: "1 aventure personnalisée pour ton petit héros.",
        2: "2 aventures personnalisées, un même héros.",
        3: "3 aventures personnalisées — le cadeau complet.",
    }

    for col, number in zip(cols, [1, 2, 3]):
        with col:
            selected = st.session_state.pack == number
            popular = number == 3

            st.markdown(f"""
            <div class="offer-card {'selected' if selected else ''} {'popular' if popular else ''}">
                <div class="offer-name">
                    {PACK_ICONS[number]} {PACK_NAMES[number]}
                </div>
                <div class="offer-desc">{descriptions[number]}</div>
                <div class="offer-price">💻 Digital — <strong>{PRICES[number]['digital']} DH</strong></div>
                <div class="offer-price">📚 Imprimé — <strong>{PRICES[number]['print']} DH</strong></div>
                <div class="offer-price">🎁 Digital + Imprimé — <strong>{PRICES[number]['both']} DH</strong></div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(
                "✓ Sélectionné" if selected else "Choisir ce pack",
                key=f"select_pack_{number}",
                use_container_width=True
            ):
                st.session_state.pack = number
                st.rerun()

    st.markdown("### 🎁 Comment veux-tu recevoir tes aventures ?")

    st.session_state.format = st.radio(
        "Format",
        ["digital", "print", "both"],
        horizontal=True,
        format_func=lambda x: FORMAT_NAMES[x],
        index=["digital", "print", "both"].index(st.session_state.format)
    )

    price = PRICES[st.session_state.pack][st.session_state.format]

    st.markdown(f"""
    <div class="summary">
        <b>Pack choisi :</b> {PACK_NAMES[st.session_state.pack]} — {st.session_state.pack} aventure(s)<br>
        <b>Format :</b> {FORMAT_NAMES[st.session_state.format]}
        <div class="total">{price} DH</div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    if st.button("Continuer →", use_container_width=True, type="primary"):
        st.session_state.step = 2
        st.rerun()

# ============================================================
# ETAPE 2 — MON HEROS
# ============================================================
elif st.session_state.step == 2:

    st.markdown('<div class="section-title">🧒 Présente-nous ton petit héros</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-text">Une seule photo suffit, même pour un pack de 3 aventures.</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns(2)

    with left:
        st.session_state.child_name = st.text_input(
            "Prénom de l'enfant",
            value=st.session_state.child_name,
            placeholder="Ex. Zayd"
        )

        st.session_state.customer_phone = st.text_input(
            "📱 Téléphone / WhatsApp du parent",
            value=st.session_state.customer_phone,
            placeholder="Ex. 0612345678",
            help="Utilisé uniquement pour le suivi de la commande et le contact WhatsApp."
        )

        st.session_state.customer_email = st.text_input(
            "📧 E-mail du parent",
            value=st.session_state.customer_email,
            placeholder="Ex. parent@email.com",
            help="Utilisé pour le suivi de la commande et l'envoi du livre numérique."
        )

        st.session_state.age = st.number_input(
            "Âge",
            min_value=3,
            max_value=14,
            value=st.session_state.age,
            step=1
        )

        st.session_state.language = st.selectbox(
            "Langue du livre",
            LANGUAGES,
            index=LANGUAGES.index(st.session_state.language)
        )

    with right:
        st.session_state.photo = st.file_uploader(
            "📷 Photo de l'enfant",
            type=["jpg", "jpeg", "png"],
            help="Cette photo servira de référence pour créer le personnage."
        )

        st.info(
            "🔒 La photo est utilisée comme référence pour le personnage. "
            "Elle n'est pas destinée à être affichée publiquement."
        )

    st.write("")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("← Retour", use_container_width=True):
            st.session_state.step = 1
            st.rerun()

    with c2:
        if st.button("Continuer →", use_container_width=True, type="primary"):
            errors = []

            if not st.session_state.child_name.strip():
                errors.append("Veuillez indiquer le prénom de l'enfant.")

            phone_digits = "".join(ch for ch in st.session_state.customer_phone if ch.isdigit())
            if len(phone_digits) < 9:
                errors.append("Veuillez indiquer un numéro de téléphone/WhatsApp valide.")

            email = st.session_state.customer_email.strip()
            if not email or "@" not in email or "." not in email.split("@")[-1]:
                errors.append("Veuillez indiquer une adresse e-mail valide.")

            if st.session_state.photo is None:
                errors.append("Veuillez ajouter une photo de l'enfant.")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                st.session_state.step = 3
                st.rerun()

# ============================================================
# ETAPE 3 — AVENTURES
# ============================================================
elif st.session_state.step == 3:

    pack = st.session_state.pack

    st.markdown('<div class="section-title">📚 Imagine ses aventures</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-text">{PACK_NAMES[pack]} — {pack} aventure(s) pour {st.session_state.child_name}.</div>',
        unsafe_allow_html=True
    )

    # Synchronisation stricte : 1 pack = 1/2/3 aventures.
    # On conserve les aventures déjà saisies et on ajoute/supprime uniquement
    # ce qui est nécessaire.
    while len(st.session_state.adventures) < pack:
        st.session_state.adventures.append({
            "theme": THEMES[0],
            "custom": "",
            "idea": "",
            "quality": ""
        })

    if len(st.session_state.adventures) > pack:
        st.session_state.adventures = st.session_state.adventures[:pack]

    for i in range(pack):
        st.markdown(f"### {'🎮' if i == 0 else '🚀' if i == 1 else '🐉'} Aventure {i + 1}")

        c1, c2 = st.columns(2)

        with c1:
            theme = st.selectbox(
                "Thème",
                THEMES,
                index=THEMES.index(st.session_state.adventures[i]["theme"]),
                key=f"adventure_theme_{i}"
            )
            st.session_state.adventures[i]["theme"] = theme

            if theme == "✨ Mon propre thème":
                custom = st.text_input(
                    "Décris ton thème",
                    value=st.session_state.adventures[i]["custom"],
                    placeholder="Ex. Une aventure dans un royaume de nuages...",
                    key=f"custom_theme_{i}"
                )
                st.session_state.adventures[i]["custom"] = custom

        with c2:
            idea = st.text_area(
                "Une idée pour son aventure (facultatif)",
                value=st.session_state.adventures[i]["idea"],
                placeholder="Ex. Il doit réussir trois défis pour rentrer chez lui.",
                height=100,
                key=f"adventure_idea_{i}"
            )
            st.session_state.adventures[i]["idea"] = idea

        quality = st.text_input(
            "Une qualité de l'enfant (facultatif)",
            value=st.session_state.adventures[i]["quality"],
            placeholder="Ex. courageux, curieux, généreux...",
            key=f"adventure_quality_{i}"
        )
        st.session_state.adventures[i]["quality"] = quality

        if i < pack - 1:
            st.divider()

    st.write("")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("← Retour", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

    with c2:
        if st.button("✨ Créer mes couvertures", use_container_width=True, type="primary"):
            errors = []

            for i, adventure in enumerate(st.session_state.adventures, start=1):
                if adventure["theme"] == "✨ Mon propre thème" and not adventure["custom"].strip():
                    errors.append(f"Veuillez décrire le thème de l'aventure {i}.")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                try:
                    create_preview_covers()
                    st.session_state.step = 4
                    st.rerun()
                except Exception as error:
                    st.error(f"La création des couvertures n’a pas pu être terminée : {error}")
                    st.info("Vérifie les secrets OPENAI_API_KEY, SUPABASE_URL et SUPABASE_SECRET_KEY dans Streamlit.")

# ============================================================
# ETAPE 4 — APERCU & COMMANDE
# ============================================================
elif st.session_state.step == 4:

    pack = st.session_state.pack
    fmt = st.session_state.format
    price = PRICES[pack][fmt]
    name = st.session_state.child_name
    adventures = st.session_state.adventures
    # Liste exacte des aventures correspondant au pack sélectionné.
    selected_adventures = list(adventures[:pack])

    st.markdown(
        f'<div class="section-title">🎉 {PACK_NAMES[pack]} — Voici les couvertures de tes livres</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="section-text">Un aperçu de chaque aventure. Les pages intérieures restent verrouillées.</div>',
        unsafe_allow_html=True
    )

    cover_paths = st.session_state.cover_paths

    if not cover_paths:
        st.warning("Aucune couverture n'a encore été générée.")
        if st.button("← Retour aux aventures", use_container_width=True):
            st.session_state.step = 3
            st.rerun()
        st.stop()

    # Les titres générés sont propres à chaque aventure.
    title_items = []
    for i, adventure in enumerate(selected_adventures, start=1):
        title = adventure.get("title")
        if title:
            title_items.append(f"<b>Aventure {i} :</b> {title}")
    if title_items:
        st.markdown(
            '<div style="text-align:center;color:#555;margin:8px 0 18px;">'
            + " &nbsp;&nbsp;•&nbsp;&nbsp; ".join(title_items)
            + "</div>",
            unsafe_allow_html=True
        )

    # Affichage strict : chaque couverture devient son propre livre 3D.
    # 1 livre = 1 colonne, 2 livres = 2 colonnes, 3 livres = 3 colonnes.
    books_html = '<div class="book-row">'

    for i, cover_path in enumerate(cover_paths, start=1):
        adventure_title = st.session_state.adventures[i - 1].get(
            "title",
            f"Aventure {i}"
        )
        image_bytes = Path(cover_path).read_bytes()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        books_html += f"""
        <div class="book-wrap">
            <div class="book-number">📕 Livre {i}</div>

            <div class="book-3d">
                <div class="book-pages"></div>
                <div class="book-spine"></div>
                <div class="book-top-edge"></div>
                <div class="book-bottom-edge"></div>
                <div class="book-gold-line"></div>

                <img
                    class="book-cover-image"
                    src="data:image/png;base64,{image_b64}"
                    alt="Couverture personnalisée du livre {i}"
                >
            </div>

            <div class="book-bottom-shadow"></div>
            <div class="book-caption">{adventure_title} • Couverture personnalisée</div>
        </div>
        """

    books_html += "</div>"

    # Streamlit peut afficher le HTML complexe comme du texte dans certains
    # cas. components.html garantit ici le rendu réel du mockup 3D.
    books_document = f'''
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 22px 10px 30px;
            background: transparent;
            font-family: Arial, sans-serif;
        }}

        .book-row {{
            display: flex;
            justify-content: center;
            align-items: flex-end;
            gap: 48px;
            flex-wrap: wrap;
            width: 100%;
        }}

        .book-wrap {{
            width: 245px;
            text-align: center;
            perspective: 1400px;
        }}

        .book-number {{
            display: inline-block;
            background: rgba(255,255,255,.97);
            padding: 7px 15px;
            border-radius: 999px;
            color: #38384d;
            font-size: 12px;
            font-weight: 700;
            box-shadow: 0 7px 22px rgba(34,34,65,.12);
            margin-bottom: 13px;
        }}

        .book-3d {{
            position: relative;
            width: 220px;
            height: 325px;
            margin: 0 auto;
            transform-style: preserve-3d;
            transform: rotateY(-17deg) rotateX(3deg) rotateZ(-1deg);
            transition: transform .35s ease;
            filter:
                drop-shadow(18px 25px 17px rgba(35,35,60,.22))
                drop-shadow(2px 4px 5px rgba(35,35,60,.12));
        }}

        .book-wrap:hover .book-3d {{
            transform: rotateY(-9deg) rotateX(1deg);
        }}

        .book-cover-image {{
            position: absolute;
            left: 13px;
            top: 0;
            width: 207px;
            height: 325px;
            object-fit: cover;
            object-position: center;
            display: block;
            border-radius: 2px 12px 12px 2px;
            z-index: 8;
            border: 1px solid rgba(20,20,30,.18);
            box-shadow:
                inset -7px 0 0 rgba(255,255,255,.12),
                inset 4px 0 0 rgba(0,0,0,.13);
        }}

        .book-spine {{
            position: absolute;
            left: 0;
            top: 1px;
            width: 17px;
            height: 323px;
            z-index: 10;
            border-radius: 5px 0 0 5px;
            background: linear-gradient(
                90deg,
                rgba(15,15,20,.72),
                rgba(255,255,255,.22),
                rgba(20,20,30,.30),
                rgba(255,255,255,.18),
                rgba(10,10,15,.55)
            );
            box-shadow: inset -1px 0 rgba(255,255,255,.32);
        }}

        .book-pages {{
            position: absolute;
            right: -13px;
            top: 7px;
            width: 17px;
            height: 311px;
            z-index: 2;
            border-radius: 0 5px 5px 0;
            background: repeating-linear-gradient(
                to bottom,
                #fffef9 0px,
                #fffef9 3px,
                #e5e2da 4px,
                #fffef9 6px
            );
            box-shadow: 3px 5px 8px rgba(0,0,0,.22);
        }}

        .book-top-edge {{
            position: absolute;
            left: 13px;
            top: -5px;
            width: 207px;
            height: 7px;
            z-index: 7;
            border-radius: 8px 12px 0 0;
            background: linear-gradient(
                180deg,
                rgba(255,255,255,.55),
                rgba(0,0,0,.10)
            );
        }}

        .book-bottom-edge {{
            position: absolute;
            left: 13px;
            bottom: -5px;
            width: 207px;
            height: 8px;
            z-index: 7;
            border-radius: 0 0 12px 8px;
            background: linear-gradient(
                180deg,
                rgba(0,0,0,.16),
                rgba(255,255,255,.28)
            );
        }}

        .book-gold-line {{
            position: absolute;
            left: 18px;
            top: 5px;
            width: 197px;
            height: 2px;
            z-index: 12;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255,215,130,.75),
                transparent
            );
        }}

        .shadow {{
            width: 225px;
            height: 30px;
            margin: -1px auto 0;
            background: radial-gradient(
                ellipse,
                rgba(24,24,40,.30),
                rgba(24,24,40,.08) 45%,
                transparent 72%
            );
            filter: blur(5px);
        }}

        .caption {{
            margin-top: 7px;
            color: #666;
            font-size: 12px;
            font-weight: 600;
        }}
    </style>
    </head>
    <body>
        {books_html}
    </body>
    </html>
    '''

    components.html(books_document, height=470, scrolling=False)

    # Contrôle silencieux utile pendant le développement.
    # Le client ne voit pas ce détail.
    if len(cover_paths) != pack:
        st.error(
            f"Une couverture manque. {len(cover_paths)} couverture(s) générée(s) "
            f"sur {pack} demandée(s)."
        )

    st.markdown("""
    <div class="lock-box">
        <div class="lock-title">🔒 Le livre complet est réservé à la commande</div>
        <div class="lock-text">
            Après validation de la commande, nous préparons les PDF complets.
            Pour les commandes imprimées, les livres sont ensuite regroupés dans un seul colis.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">🧾 Ta commande</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="summary">
        <b>Héros :</b> {name}<br>
        <b>Pack :</b> {PACK_NAMES[pack]} — {pack} aventure(s)<br>
        <b>Format :</b> {FORMAT_NAMES[fmt]}<br>
        <b>Langue :</b> {st.session_state.language}
        <div class="total">Total : {price} DH</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(
        "💬 Valider ma commande sur WhatsApp",
        use_container_width=True,
        type="primary"
    ):
        if WHATSAPP_NUMBER == "212603983800":
            st.error("Configure ton numéro WhatsApp dans app.py avant de continuer.")
        else:
            try:
                order_file = save_order_metadata()
            except Exception as error:
                st.error(f"Impossible d'enregistrer la commande : {error}")
                st.stop()

            details = []

            for i, adventure in enumerate(adventures[:pack], start=1):
                theme = (
                    adventure["custom"]
                    if adventure["theme"] == "✨ Mon propre thème"
                    else adventure["theme"]
                )

                details.append(
                    f"Aventure {i}: {theme}\n"
                    f"Titre: {adventure.get('title') or 'À confirmer'}\n"
                    f"Idée: {adventure['idea'] or 'Aucune'}\n"
                    f"Qualité: {adventure['quality'] or 'Aucune'}"
                )

            message = (
                "Bonjour My Little Hero 👋\n\n"
                "Je souhaite commander mon livre personnalisé.\n\n"
                f"👦 Enfant : {name}\n"
                f"📱 WhatsApp : {st.session_state.customer_phone}\n"
                f"📧 E-mail : {st.session_state.customer_email}\n"
                f"🎂 Âge : {st.session_state.age} ans\n"
                f"🌍 Langue : {st.session_state.language}\n"
                f"📦 Pack : {pack} aventure(s)\n"
                f"🎁 Format : {FORMAT_NAMES[fmt]}\n"
                f"💰 Total : {price} DH\n\n"
                + "\n\n".join(details)
                + "\n\nJe souhaite valider ma commande."
            )

            url = f"https://wa.me/{WHATSAPP_NUMBER}?text={urllib.parse.quote(message)}"

            st.success("Votre commande est prête et enregistrée.")
            st.caption(f"Référence de commande : {get_order_number()}")
            st.markdown(
                f'<a href="{url}" target="_blank" style="display:block;text-align:center;'
                'background:#25D366;color:white;padding:14px;border-radius:14px;'
                'text-decoration:none;font-weight:700;margin-top:10px">'
                '💬 Ouvrir WhatsApp</a>',
                unsafe_allow_html=True
            )

    if st.button("← Modifier ma commande", use_container_width=True):
        st.session_state.step = 3
        st.rerun()

st.divider()

st.markdown(
    '<div class="footer">🌟 My Little Hero — Une activité créative pour lire, imaginer et colorier.</div>',
    unsafe_allow_html=True
)
