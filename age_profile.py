"""Shared age-dependent art direction for printable coloring illustrations."""


def coloring_instruction(age):
    age = int(age)
    if age <= 5:
        detail = "3 à 5 ans : difficulté très facile, contours épais, très grandes zones fermées, peu d’objets et aucun petit motif."
    elif age <= 8:
        detail = "6 à 8 ans : difficulté facile, contours bien marqués, grandes zones, quelques détails simples et décor peu chargé."
    elif age <= 12:
        detail = "9 à 12 ans : difficulté intermédiaire, contours nets, détails variés et motifs de taille moyenne, décor plus développé."
    else:
        detail = "13 à 16 ans : difficulté avancée adaptée aux adolescents, style illustré moins enfantin, proportions crédibles, décors élaborés, motifs et accessoires plus fins et variés."
    return (f"Coloriage adapté à l’âge exact de {age} ans. {detail} "
        "Conserver des zones fermées assez grandes pour les crayons à taille A4 ; "
        "éviter les microdétails illisibles, le fouillis et les zones impossibles à colorier. "
        "Noir et blanc au trait sur fond blanc, sans ombres, gris, hachures ni aplats noirs.")
