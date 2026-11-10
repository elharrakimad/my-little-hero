# Packs — 10 novembre 2026

`packs.json` est le catalogue serveur. `packs.js` en reprend les données pour le navigateur ; le test `tests/packs.test.cjs` vérifie leur égalité et les grilles HTML.

- Digital : 79 DH, PDF, choix couleur ou coloriage.
- Petit Artiste : 149 DH, A4 coloriage + PDF.
- Mon Histoire : 199 DH, A5 couleur + PDF.
- Super Héros : 249 DH, A5 couleur + A4 coloriage + PDF, sans crayons ni emballage cadeau.
- Ultimate Hero : 349 DH, ces deux livres + crayons + boîte rigide personnalisée + carte cadeau + PDF.

Livraison séparée : montant confirmé avec le client avant paiement. `total_price` reste le prix du pack hors livraison. Aucun frais de livraison inventé, aucune modification des commandes existantes.

Les packs à deux livres demandent deux univers : le premier est produit en couleur, le second en coloriage. Le worker utilise `adventures[].book_style`. Le PDF couleur peut être imprimé au format A5 ; le PDF coloriage au format A4.

Le parcours existant reste aperçu → commande WAITING_FOR_PAYMENT → confirmation WhatsApp → validation du paiement par l’équipe. Il n’y a pas de passerelle de paiement automatisée dans ce dépôt.

Déploiement : mettre à jour l’API (api.py, packs.py, packs.json) et Streamlit, puis les fichiers statiques. Le navigateur vérifie le pack et le montant retournés par l’API avant d’activer la commande ; un ancien serveur ne permet pas de confirmer un montant erroné. Vérifier le déploiement séparément du push Git.

Tests sans frais IA ni écritures en production : unittest tests/test_order_details.py et tests/test_child_profile.py ; node --test tests/packs.test.cjs tests/preview-origin.test.cjs.
