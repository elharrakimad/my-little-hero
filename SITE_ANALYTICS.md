# Tableau de bord du flux

## Essai local sans production

Lancer `local_analytics_test.py` avec Streamlit (adresse 127.0.0.1:8501), puis ouvrir le site de test à 127.0.0.1:5500 depuis le bouton. Les événements proviennent des clics locaux et sont stockés dans `tmp/analytics-local.sqlite`. La génération IA est désactivée dans cet essai. Aucun secret ni accès Supabase n’est nécessaire.

## Activation en ligne

1. Exécuter `database/site_events.sql` dans le projet Supabase utilisé par l’API et l’admin.
2. Déployer l’API avec `site_analytics.py`, puis l’admin avec `analytics_dashboard.py` et les fichiers frontend modifiés, dont `analytics.js`.
3. Ouvrir l’admin authentifié, rubrique **Flux du site**. Actualisation automatique toutes les 5 secondes ; présence envoyée toutes les 60 secondes pour les onglets visibles.
4. Parcourir le site, vérifier l’apparition de la visite et du démarrage de création. Vérifier que les rôles anon/authenticated ne peuvent pas lire `site_events`.

Les chiffres sont réels, sans données de démonstration. Aucun historique de visites antérieur au déploiement n’est disponible. Do Not Track est respecté. La session aléatoire est propre à l’onglet, conservée en sessionStorage. Aucun champ personnel, photo, URL, référent ni adresse IP n’est enregistré dans la table. Les logs d’hébergement sont gérés séparément.

Les événements navigateur sont indicatifs : blocage réseau, fermeture, robots ou requêtes fabriquées peuvent fausser les chiffres. Les clics WhatsApp ne sont pas des ventes. Les paiements ne sont pas reliés aux sessions dans cette version. Le statut réel reste dans les commandes.

Le point d’entrée accepte uniquement une liste de champs et d’événements autorisés, et déduplique par UUID. Avant un trafic important, ajouter une limitation de débit à la passerelle hébergeur. Prévoir une purge régulière des événements de plus de 30 jours selon les besoins de conservation.

Contrôles locaux : `python -m unittest discover -s tests -p test_site_analytics.py` ; `node --check analytics.js`.
