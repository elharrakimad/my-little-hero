import base64
import io
import json
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from supabase import create_client

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


def save_order_to_supabase(order_ref, name, age, language, pack, themes, reference_bytes, cover_files):
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
    for index, theme_value in enumerate(themes, start=1):
        clean_theme = theme_value
        adventures.append({
            "number": index,
            "theme": clean_theme,
            "idea": "",
            "quality": "",
            "title": "",
        })

    row = {
        "order_ref": order_ref,
        "parent_name": None,
        "parent_phone": None,
        "parent_email": None,
        "child_name": name,
        "child_age": age,
        "language": language,
        "pack": {1: "LITTLE HERO", 2: "SUPER HERO", 3: "HERO GIFT"}.get(pack, "LITTLE HERO"),
        "adventure_count": len(themes),
        "total_price": {1: 69, 2: 119, 3: 159}.get(pack, 69),
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
        "العربية": "اكتب عنوان الكتاب باللغة العربية.",
    }.get(language, "Écris le titre dans la langue demandée.")


def generate_title(client, name, age, theme, language):
    prompt = f"""
Tu es le directeur éditorial de My Little Hero, une marque de livres
personnalisés pour enfants.

Invente UN SEUL titre de livre original pour cette aventure.

ENFANT : {name}, {age} ans
THÈME : {theme}

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
    return title[:120]


def generate_cover(client, reference_bytes, name, age, theme, language, title):
    if language == "English":
        subtitle = "Personalized Coloring Book"
    elif language == "Español":
        subtitle = "Libro de colorear personalizado"
    elif language == "العربية":
        subtitle = "كتاب تلوين مخصص"
    else:
        subtitle = "Livre de coloriage personnalisé"

    prompt = f"""
Crée la couverture couleur professionnelle d'un livre jeunesse personnalisé.

Utilise l'image fournie comme référence principale du personnage.
Le personnage doit rester reconnaissable : même visage général,
même coiffure, même âge apparent et même apparence générale.

PERSONNAGE : {name}, {age} ans
THÈME : {theme}

Crée une scène de couverture joyeuse, magique et aventureuse,
avec l'enfant clairement au premier plan et un décor riche inspiré du thème.

STYLE : illustration professionnelle de livre jeunesse, très colorée,
chaleureuse, joyeuse, composition verticale, rendu premium.
Personnages et univers totalement originaux.
Aucun personnage existant, aucun logo de marque, aucun watermark.

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
):
    name = child_name.strip()
    age = child_age.strip()
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
    selected_themes = selected_themes[:3]

    if not name or not age or not selected_themes:
        raise HTTPException(status_code=400, detail="Informations incomplètes.")

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

IMPORTANT : conserver les traits généraux du visage, la coiffure,
l'apparence générale reconnaissable et l'âge apparent.
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
        for selected_theme in selected_themes:
            title = generate_title(client, name, age, selected_theme, language)
            cover_bytes = generate_cover(
                client, reference_bytes, name, age, selected_theme, language, title
            )
            cover_bytes_list.append(cover_bytes)
            covers.append({
                "title": title,
                "theme": selected_theme,
                "cover_data_url": "data:image/png;base64," + base64.b64encode(cover_bytes).decode("ascii"),
            })

        order_ref = datetime.now().strftime("MLH-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6].upper()
        save_order_to_supabase(order_ref, name, age, language, len(selected_themes), selected_themes, reference_bytes, cover_bytes_list)

        return {
            "ok": True,
            "order_ref": order_ref,
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
