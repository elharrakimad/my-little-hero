import base64
import io
import json
import os
import uuid
import re
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from supabase import create_client
from packs import get_pack
from child_profile import gender_instruction
from character_identity import IDENTITY_INSTRUCTION
from story_reference import visual_reference_instruction
from anime_cast import anime_cast_instruction
from book_style import validate_book_style, cover_subtitle

app = FastAPI(title="My Little Hero API", version="0.1.0")

# GitHub Pages frontend needs to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://my-little-hero.online",
        "https://www.my-little-hero.online",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_PHOTO_BYTES = 8 * 1024 * 1024


def get_supabase_client():
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_SECRET_KEY", "").strip()
           or os.getenv("SUPABASE_SERVICE_KEY", "").strip())
    if not url or not key:
        raise RuntimeError("Supabase is not configured.")
    return create_client(url, key)


def validate_parent_contact(phone, email=""):
    phone, email = phone.strip(), email.strip()
    digits = re.sub(r"\D", "", phone)
    if not re.fullmatch(r"\+?[0-9() .-]+", phone) or not 7 <= len(digits) <= 15:
        raise HTTPException(status_code=400, detail="Un numéro de téléphone valide est obligatoire.")
    if email and (len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)):
        raise HTTPException(status_code=400, detail="Veuillez vérifier votre adresse e-mail.")
    return ("+" if phone.startswith("+") else "") + digits, email


def resolve_order_themes(themes, custom_theme=""):
    custom_theme = custom_theme.strip()
    result = []
    for theme in themes:
        if theme in {"✨ Mon propre thème", "Mon propre thème"}:
            if not custom_theme or len(custom_theme) > 600:
                raise HTTPException(status_code=400, detail="Décrivez votre thème personnalisé (600 caractères maximum).")
            result.append((f"Thème personnalisé : {custom_theme}", custom_theme))
        else:
            result.append((theme, ""))
    return result


def save_order_to_supabase(order_ref, name, age, language, pack, covers, reference_bytes, cover_files, child_gender="", parent_phone="", parent_email="", book_style="coloring"):
    offer = get_pack(pack)
    supabase = get_supabase_client()
    bucket = "my-little-hero-files"
    root = f"orders/{order_ref}"
    reference_path = f"{root}/reference/character_reference.png"
    supabase.storage.from_(bucket).upload(
        reference_path, reference_bytes,
        file_options={"content-type": "image/png", "upsert": "true"},
    )
    cover_paths = []
    for index, cover_bytes in enumerate(cover_files, start=1):
        path = f"{root}/covers/cover_{index:02d}.png"
        supabase.storage.from_(bucket).upload(
            path, cover_bytes,
            file_options={"content-type": "image/png", "upsert": "true"},
        )
        cover_paths.append(path)

    adventures = []
    for index, cover in enumerate(covers, start=1):
        adventures.append({
            "number": index,
            "child_gender": child_gender,
            "book_style": cover.get("book_style", validate_book_style(book_style)),
            "digital_copy_included": offer["pdf_included"],
            "theme": cover.get("theme", ""),
            "idea": cover.get("idea", ""),
            "quality": "",
            "title": cover.get("title", ""),
        })
        if offer.get("paired_story") and index == 2:
            adventures[-1].update(paired_version="same-scenes-v1", shared_story_from=1, image_only=True)

    row = {
        "order_ref": order_ref,
        "parent_name": None,
        "parent_phone": parent_phone or None,
        "parent_email": parent_email or None,
        "child_name": name,
        "child_age": age,
        "language": language,
        "pack": offer["name"],
        "adventure_count": len(covers),
        "total_price": offer["price"],
        "status": "WAITING_FOR_PAYMENT",
        "adventures": adventures,
        "reference_path": reference_path,
        "cover_paths": cover_paths,
        "generated_files": [],
    }
    supabase.table("orders").insert(row).execute()
    return order_ref, reference_path, cover_paths


def get_openai_client():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=key)


def image_file(data: bytes, filename: str):
    f = io.BytesIO(data)
    f.name = filename
    f.seek(0)
    return f


def language_instruction(language: str) -> str:
    return {
        "Français": "Écris le titre en français.",
        "English": "Write the title in English.",
        "Español": "Escribe el título en español.",
        "العربية": "اكتب عنوان الكتاب بالعربية الفصحى فقط، دون كلمات فرنسية أو إنجليزية. اكتب اسم الطفل بحروف عربية أيضًا.",
    }.get(language, "Écris le titre dans la langue demandée.")


def generate_title(client, name, age, theme, language, child_gender=""):
    prompt = f"""
Tu es le directeur éditorial de My Little Hero, une marque de livres
personnalisés pour enfants.

Invente UN SEUL titre de livre original pour cette aventure.

ENFANT : {name}, {age} ans
THÈME : {theme}
{gender_instruction(child_gender)}

{language_instruction(language)}

Le titre doit :
- être court, mémorable et adapté à un livre jeunesse ;
- être directement inspiré du thème ;
- être différent de "L'aventure de {name}" ;
- donner envie de découvrir l'histoire ;
- être original ;
- ne contenir aucun personnage, marque, film, série, jeu vidéo ou univers protégé ;
- ne contenir ni guillemets, ni emoji, ni sous-titre.

Réponds uniquement avec le titre final, sur une seule ligne.
"""
    response = client.responses.create(model="gpt-6-luna", input=prompt)
    title = response.output_text.strip().replace("\n", " ").strip('"“”')
    if not title:
        raise ValueError("L'IA n'a pas généré de titre.")
    if language == "العربية" and (re.search(r"[A-Za-z\u00c0-\u024f\u1e00-\u1eff]", title)
            or not re.search(r"[\u0621-\u064a\u066e-\u06d3]", title)):
        raise ValueError("Le titre généré mélange plusieurs langues. Aucune couverture n’a été lancée.")
    return title[:120]


def generate_cover(client, reference_bytes, name, age, theme, language, title, child_gender="", book_style="coloring"):
    subtitle = cover_subtitle(language, book_style)
    prompt = f"""
Crée la couverture couleur professionnelle d'un livre jeunesse personnalisé.

Utilise l'image fournie comme référence principale du personnage.
Le personnage doit rester reconnaissable : même visage général,
même coiffure, même âge apparent et même apparence générale.
{IDENTITY_INSTRUCTION}

PERSONNAGE : {name}, {age} ans
THÈME : {theme}
{gender_instruction(child_gender)}

Crée une scène de couverture joyeuse, magique et aventureuse,
avec l'enfant clairement au premier plan et un décor riche inspiré du thème.

STYLE : illustration professionnelle de livre jeunesse, très colorée,
chaleureuse, joyeuse, composition verticale, rendu premium.
{visual_reference_instruction(theme)}
{anime_cast_instruction(theme, book_style)}
Aucun watermark ni texte supplémentaire.

AFFICHER EXACTEMENT CES TEXTES :
"{title}"
"{subtitle}"

Les textes doivent être grands, lisibles et bien intégrés.
Ne pas ajouter d'autres textes.
"""
    result = client.images.edit(
        model="gpt-image-2",
        image=[image_file(reference_bytes, "character_reference.png")],
        prompt=prompt,
        size="1024x1536",
        quality="medium",
    )
    return base64.b64decode(result.data[0].b64_json)


@app.get("/health")
def health():
    return {"ok": True, "service": "my-little-hero-api"}


@app.post("/api/preview-cover")
async def preview_cover(
    child_name: str = Form(...),
    child_age: str = Form(...),
    language: str = Form("Français"),
    theme: str = Form(""),
    themes: str = Form(""),
    photo: UploadFile = File(...),
    child_gender: str = Form(...),
    parent_phone: str = Form(...),
    parent_email: str = Form(""),
    custom_theme: str = Form(""),
    book_style: str = Form("coloring"),
    pack_id: int = Form(1),
):
    try:
        book_style = validate_book_style(book_style)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        offer = get_pack(pack_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    parent_phone, parent_email = validate_parent_contact(parent_phone, parent_email)
    child_gender = child_gender.strip()
    if child_gender not in {"girl", "boy"}:
        raise HTTPException(status_code=400, detail="Veuillez choisir fille ou garçon.")
    name = child_name.strip()
    age = child_age.strip()
    match = re.search(r"\d+", age)
    age_value = int(match.group()) if match else None
    selected_theme = theme.strip()
    selected_themes = []
    if themes.strip():
        try:
            parsed = json.loads(themes)
            if isinstance(parsed, list):
                selected_themes = [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            selected_themes = []
    if not selected_themes and selected_theme:
        selected_themes = [selected_theme]
    if len(selected_themes) != offer.get("theme_count", len(offer["styles"])):
        raise HTTPException(status_code=400, detail="Le nombre d’aventures ne correspond pas au pack.")
    if pack_id == 1 and book_style != "coloring":
        raise HTTPException(status_code=400, detail="Le pack Digital comprend uniquement une histoire à colorier.")
    styles = offer["styles"]

    if not name or not age or age_value is None or not selected_themes:
        raise HTTPException(status_code=400, detail="Informations incomplètes.")
    if not 3 <= age_value <= 16:
        raise HTTPException(status_code=400, detail="L’âge doit être compris entre 3 et 16 ans.")

    resolved_themes = resolve_order_themes(selected_themes, custom_theme)

    data = await photo.read()
    if not data:
        raise HTTPException(status_code=400, detail="Photo manquante.")
    if len(data) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail="La photo doit faire moins de 8 Mo.")

    content_type = photo.content_type or ""
    if content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=400, detail="Format photo non accepté.")

    try:
        client = get_openai_client()
        # We create the visual character reference first, then the cover.
        reference_result = client.images.edit(
            model="gpt-image-2",
            image=[image_file(data, photo.filename or "enfant.jpg")],
            prompt=f"""
Crée une référence visuelle cohérente du personnage principal d'un livre jeunesse personnalisé.
Utilise la photo fournie uniquement comme référence visuelle de l'enfant.
L'enfant s'appelle {name} et a {age} ans.
{gender_instruction(child_gender)}

IMPORTANT : conserver les traits généraux du visage, la coiffure,
l'apparence générale reconnaissable et l'âge apparent.
{IDENTITY_INSTRUCTION}
Créer un personnage original, avec une tenue simple et neutre.
Illustration jeunesse professionnelle, composition verticale,
personnage visible en entier, arrière-plan simple.
Aucun texte, logo ou watermark. Aucun personnage ou univers protégé.
""",
            size="1024x1536",
            quality="medium",
        )
        reference_bytes = base64.b64decode(reference_result.data[0].b64_json)

        covers = []
        cover_bytes_list = []
        for book_index, book_style in enumerate(styles):
            selected_theme, client_idea = resolved_themes[0 if offer.get("paired_story") else book_index]
            if book_index and offer.get("paired_story"):
                title, cover_bytes = covers[0]["title"], cover_bytes_list[0]
            else:
                title = generate_title(client, name, age, selected_theme, language, child_gender)
                cover_bytes = generate_cover(
                    client, reference_bytes, name, age, selected_theme, language, title, child_gender, book_style
                )
            cover_bytes_list.append(cover_bytes)
            covers.append({
                "title": title,
                "book_style": book_style,
                "theme": selected_theme,
                "idea": client_idea,
                "cover_data_url": "data:image/png;base64," + base64.b64encode(cover_bytes).decode("ascii"),
            })

        order_ref = datetime.now().strftime("MLH-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6].upper()
        save_order_to_supabase(order_ref, name, age_value, language, pack_id, covers, reference_bytes, cover_bytes_list, child_gender, parent_phone, parent_email, book_style)

        return {
            "ok": True,
            "order_ref": order_ref,
            "pack_id": pack_id,
            "total_price": offer["price"],
            "covers": covers,
        }

    except HTTPException:
        raise
    except Exception as exc:
        # Do not expose OpenAI/internal details to the customer.
        print(f"preview-cover error: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Impossible de générer l'aperçu pour le moment. Veuillez réessayer."
        )
