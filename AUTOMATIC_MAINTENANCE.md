# Nettoyage automatique et mémoire

Politique autorisée : uniquement les commandes `DELIVERED` (Livrée). Un clic
sur un téléchargement ne prouve pas que le fichier est arrivé sur l’ordinateur.
Les commandes prêtes, expédiées, annulées, interrompues ou en cours restent intactes.

Le worker vérifie les caches à vide au démarrage, puis toutes les cinq minutes,
par lots limités à 50 livres. Il ne nettoie jamais avec un journal de production
actif. Pour chaque livre, il vérifie que le chemin du PDF est déclaré dans la
commande, télécharge le PDF privé en flux vers un fichier temporaire, vérifie
l’en-tête et la fin du fichier, puis ouvre ses pages et leurs flux avec pypdf.
Il calcule aussi une empreinte SHA-256. Tout le lot doit être vérifié avant
la première suppression ; le statut est relu juste avant chaque suppression.

Seul `/var/data/orders/<référence>/final_books/adventure_XX` est supprimé.
Les photos, références, couvertures d’aperçu, lignes de commande et PDF dans
Supabase restent en place. Aucun lien public ni secret n’est créé ou journalisé.
Un reçu est conservé dans `auto_cleanup_latest.json`, et un bilan figure dans
les logs `AUTO_CLEANUP`. Les sauvegardes ne sont pas supprimées automatiquement.
Une erreur de stockage ou de PDF conserve les caches et diffère le nettoyage.
`MLH_AUTO_CLEANUP=0` désactive le nettoyage automatique.

Le téléchargement d’un livre depuis Admin reste possible après nettoyage :
Admin recharge le PDF conservé dans le stockage privé. Refaire une mise en page
à partir des illustrations supprimées exige en revanche de restaurer ces
illustrations ou de les régénérer. Le PDF livré reste disponible.

La RAM est traitée séparément : chaque commande est générée par un processus
enfant qui se termine à la fin de la commande ; le parent n’importe pas le
moteur PDF/IA et garde le journal de reprise. Un échec ne relance pas l’IA en
boucle : la commande passe en interruption, avec les dernières étapes conservées.
Les images couleur sont intégrées au PDF depuis des JPEG temporaires réutilisés,
à leur résolution d’origine et avec la même qualité JPEG. Cela évite de garder
les pixels RGB de toutes les pages en mémoire. Aucune hausse de forfait Render.

Ces protections réduisent le risque de saturation ; elles ne garantissent pas
qu’une commande exceptionnellement lourde tienne toujours dans 512 Mo.
Vérifier la mémoire maximale lors de la prochaine génération réelle.

Inspection sans suppression : `python storage_maintenance.py --max-books 50`.
Application manuelle (uniquement après autorisation) : ajouter `--apply`.
