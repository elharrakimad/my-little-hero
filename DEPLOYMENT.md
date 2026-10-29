# Administration et génération sur Render

## Services

Le fichier `render-cloud.yaml` ajoute uniquement deux services, sans modifier
l'API existante ni le site GitHub Pages :

- `my-little-hero-admin` : administration Streamlit avec connexion par mot de passe.
- `my-little-hero-generation` : worker Linux, une seule instance, disque persistant
  de 1 Go monté sur `/var/data`, progression dans `/var/data/orders`.

Ces services utilisent les offres payantes `starter`. Vérifier et accepter le
total affiché par Render avant de créer les ressources. Les crédits OpenAI,
Supabase et les éventuels dépassements de stockage/trafic restent séparés.

## Configuration

1. Vérifier que le projet Supabase qui contient `orders` et le bucket privé
   `my-little-hero-files` est actif. Aucune migration de table n'est nécessaire.
   Le statut doit accepter les valeurs déjà utilisées par le projet : `PAID`,
   `GENERATING`, `GENERATION_INTERRUPTED`, `BOOKS_READY`.
2. Dans Render, créer un Blueprint depuis le dépôt
   `https://github.com/elharrakimad/my-little-hero`, branche `main`, avec le chemin
   **`render-cloud.yaml`**, pas `render.yaml`.
3. Saisir les secrets directement dans Render :

| Service | Variables |
| --- | --- |
| Admin | `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `MY_LITTLE_HERO_ADMIN_PASSWORD` |
| Worker | `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `OPENAI_API_KEY` |

Utiliser le même projet Supabase que l'API. Choisir un mot de passe administrateur
long et unique. Ne jamais placer ces valeurs dans GitHub, le code ou le chat.
`MLH_WORK_DIR=/var/data/orders` est déjà déclaré pour le worker.

4. Arrêter toute ancienne administration locale qui exécute encore directement
   la génération. Ne déployer qu'un seul worker avec ce disque. Ne pas lancer
   un deuxième worker ailleurs avec les mêmes commandes.
5. Avant le premier lancement, vérifier les commandes déjà au statut `PAID` :
   elles seront traitées automatiquement et consommeront des crédits OpenAI.
6. Ouvrir l'URL de l'admin fournie par Render, se connecter et vérifier la liste
   des commandes. Vérifier dans Render que le worker est en cours d'exécution.

## Utilisation depuis le téléphone

- Vérifier le paiement réellement reçu, cocher la confirmation, puis cliquer
  **Valider le paiement et générer**. Le logiciel ne vérifie pas le compte bancaire.
- `PAID` signifie en attente du worker. `GENERATING` signifie pris en charge.
  Le téléphone et le PC peuvent être éteints après la validation.
- Actualiser la liste pour consulter la progression. À `BOOKS_READY`, télécharger
  les PDF depuis l'admin (les fichiers définitifs sont dans Supabase privé).
- À `GENERATION_INTERRUPTED`, consulter les logs du worker, corriger la cause,
  puis utiliser **Remettre en file de génération**. Les livres déjà enregistrés
  ne sont pas recréés. Les histoires et pages terminées restent sur le disque.

## Reprise et limites

Le worker réclame chaque commande par une mise à jour conditionnelle
`PAID → GENERATING`. Son journal persistant permet de reprendre sa commande
après un redémarrage ; il ne modifie pas les autres commandes en cours.
Une erreur de génération est mise en pause pour éviter une boucle payante.
Les écritures d'histoires/images et le PDF final sont atomiques.

Une interruption après la réponse d'OpenAI mais avant l'enregistrement local
peut néanmoins imposer de refaire cet appel. Aucune garantie de facturation
« exactement une fois » n'est possible dans cette fenêtre.

Le disque conserve les fichiers intermédiaires, donc surveiller son espace et
l'agrandir avant saturation. Ne pas supprimer le disque lors d'un redéploiement.
Les anciennes commandes au statut `GENERATING` sans journal de ce worker ne
sont pas automatiquement relancées : vérifier que l'ancien moteur est arrêté
avant de les remettre manuellement en attente.

## Vérification après déploiement

Avec une commande de test explicitement approuvée (appels OpenAI payants), valider
le paiement, fermer l'admin, vérifier les logs, puis rouvrir l'admin et télécharger
le livre. Le test de génération complet n'est pas exécuté par les tests unitaires.
Les tests locaux utilisent des doubles, sans crédit OpenAI ni modification de DB.

Pour revenir en arrière, suspendre d'abord le worker pour éviter de mélanger
l'ancien mode de génération local et le nouveau mode cloud.
