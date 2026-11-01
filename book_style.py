"""Book rendering choice, shared by preview, orders, worker and PDF layout."""
from pathlib import Path
from age_profile import coloring_instruction


def validate_book_style(value="coloring"):
    if value not in {"coloring", "colored"}:
        raise ValueError("Type de livre invalide : choisir coloring ou colored.")
    return value


def book_output_dir(folder, style="coloring"):
    validate_book_style(style)
    return Path(folder)/"colored" if style == "colored" else Path(folder)


def illustration_direction(style, age):
    validate_book_style(style)
    if style == "coloring":
        return coloring_instruction(age)
    detail = "formes simples, composition lisible et chaleureuse" if int(age) <= 8 else "décors riches et détails adaptés, style moins enfantin pour les adolescents"
    return (f"Livre d’histoires entièrement illustré en couleur pour {age} ans : {detail}. "
        "Illustration jeunesse professionnelle entièrement colorée, palette harmonieuse et constante, "
        "vêtements, cheveux, personnages et décors colorés. Lumière douce et profondeur illustrée. "
        "Respecter exactement les couleurs de la tenue de couverture et des références des personnages. "
        "L’illustration est terminée et prête à lire, pas un dessin à colorier ni une esquisse monochrome.")


def cover_subtitle(language, style="coloring"):
    validate_book_style(style)
    if style == "colored":
        return {"English":"Personalized illustrated storybook", "Español":"Cuento ilustrado personalizado",
            "العربية":"قصة مصورة مخصصة"}.get(language, "Livre d’histoires personnalisé")
    return {"English":"Personalized coloring book", "Español":"Libro de colorear personalizado",
        "العربية":"كتاب تلوين مخصص"}.get(language, "Livre de coloriage personnalisé")


def book_style_label(style="coloring"):
    return "Histoire déjà en couleur" if style == "colored" else "Histoire à colorier"
