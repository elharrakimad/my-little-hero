"""Shared editorial instructions; never infer gender from a name or photo."""


def gender_instruction(gender):
    if gender == "girl":
        identity = "L'enfant est une fille. C'est l'héroïne : elle, la, sa."
    elif gender == "boy":
        identity = "L'enfant est un garçon. C'est le héros : il, le, son."
    else:
        return "Genre non renseigné : ne pas le déduire du prénom ou de la photo."
    return (
        identity + " Respecte ce choix dans tout le récit, les titres et les dialogues. "
        "Dans la langue demandée, emploie les pronoms et les formes grammaticales "
        "appropriés : accords des noms, adjectifs et participes, conjugaison selon "
        "le sujet et règles de possession. Ne remplace pas mécaniquement son par sa : "
        "le possessif dépend du nom possédé. Vérifie la cohérence grammaticale de "
        "chaque page avant de répondre. N'impose aucun trait de personnalité, "
        "centre d'intérêt ou apparence stéréotypés."
    )
