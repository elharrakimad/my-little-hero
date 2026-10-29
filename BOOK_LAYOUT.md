# Modèle de livre de contes à colorier

## Organisation

- `book_layout.py` : grille A4, polices, marges, étoiles vectorielles, ruban,
  répartition du récit et page souvenir. Tous les réglages sont dans les
  dataclasses `Layout` et `KeepsakeLayout`.
- `book_content.py` : lecture des 10 pages, sans modification du texte de
  l'histoire. Le bloc optionnel `SOUVENIR / Félicitations : ...` est séparé des scènes.
- `generate_book.py` : illustration sans texte, détails adaptés à l'âge,
  médaillon séparé et appel du moteur PDF déterministe.
- `book_engine.py` : chemins par aventure, reprise des étapes existantes et
  progression de la génération du médaillon. Aucun ancien livre prêt n'est
  automatiquement régénéré.

## Règles d'impression

A4 portrait, marges de 22 mm côté reliure et de 18 mm à l'extérieur.
Titres à 23 pt, récit à 14 pt et interligne de 20 pt. La zone du récit est
réservée avant l'illustration ; elle est blanche, sans encadré ni fond gris.
Un titre long agrandit la bande commune à toutes les pages du livre.

Un récit trop long est réparti, de préférence entre deux phrases, sur une page
de suite utilisant la même illustration. Aucun mot n'est supprimé et la police
n'est pas réduite. Les numéros suivent les pages imprimées. Un livre peut donc
compter plus de dix pages d'histoire si le contenu existant est long.

La page souvenir remplace l'ancienne page de fin ; elle ne remplace pas la
dixième page de l'histoire. Elle comporte un médaillon à colorier, un ruban
vectoriel, des textes sélectionnables et une surface de dessin d'environ
17 × 8,8 cm. L'apparence du personnage est fournie par la même référence que
les scènes du livre. Le médaillon nécessite une image IA supplémentaire par
aventure, puis est conservé pour les reprises.

La couverture couleur déjà validée reste la couverture. Les nouvelles règles
noir et blanc s'appliquent aux pages intérieures et à la page souvenir.

## Exemple reproductible sans clé API

```text
python examples/build_itar_sample.py
```

Crée `output/pdf/itar-maquette-livre-coloriage.pdf` avec une page de basket pour
Itar et la page souvenir. Les deux illustrations de démonstration sont dans
`examples/itar/`. Le même moteur de mise en page est utilisé en production.

Les vérifications portent sur le rendu PDF réel, les accents français, les
tailles de police, l'absence de chevauchement, les limites de page et la
conservation de tous les mots lors d'un dépassement. Cette maquette a été
vérifiée en français. L'exemple ne réécrit ni ne remplace le livre déjà livré
d'Itar et ne contient pas sa photo d'origine.
