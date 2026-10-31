"""Choose the visual direction supplied by the order, without changing API safety settings."""


def visual_reference_instruction(theme):
    detailed = "Tenue et apparence :" in str(theme) and "Adversaires ou obstacles :" in str(theme)
    if detailed:
        return (
            "Suivre la fiche de référence visuelle du thème : vêtements, couleurs, motifs, "
            "architecture, paysages, équipements et adversaires décrits. Ne pas remplacer "
            "ces détails par une tenue ou un décor générique différent. "
            "L'enfant reste le personnage principal, avec son visage, son âge et sa coiffure. "
            "Créer une nouvelle intrigue adaptée à son âge, sans reprendre un scénario existant. "
            "Ne pas ajouter de noms de personnages ou de franchises aux textes ou aux images. "
            "Les accessoires et adversaires restent adaptés à un livre jeunesse, sans blessure ni sang."
        )
    return (
        "Créer des personnages et un univers totalement originaux. "
        "Ne pas reprendre de personnage connu ni d'univers provenant d'une œuvre existante."
    )
