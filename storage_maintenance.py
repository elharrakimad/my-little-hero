"""Explicit, bounded removal of local caches after verifying private PDF backups."""
import hashlib
import json
import logging
from pathlib import Path
import re
import shutil

BUCKET = 'my-little-hero-files'


def cleanup_completed_books(db, root, plan_json):
    root = Path(root).resolve(strict=True)
    plan = json.loads(plan_json)
    if not isinstance(plan, list) or not 1 <= len(plan) <= 5:
        raise ValueError('Le nettoyage doit désigner entre un et cinq livres précis.')
    key = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()[:20]
    receipt = root / f'cleanup_{key}.json'
    if receipt.exists():
        logging.info('STORAGE_CLEANUP déjà terminé : %s', receipt.read_text())
        return json.loads(receipt.read_text())
    targets, seen = [], set()
    # Validate EVERY backup and target before removing ANY local file.
    for item in plan:
        ref, index = item['order_ref'], item['index']
        if not isinstance(ref, str) or not re.fullmatch(r'MLH-[0-9]{8}-[0-9]{6}-[A-F0-9]{6}', ref):
            raise ValueError('Référence de commande invalide.')
        if type(index) is not int or not 1 <= index <= 3 or (ref, index) in seen:
            raise ValueError('Numéro de livre invalide ou répété.')
        seen.add((ref, index))
        rows = db.table('orders').select('status,generated_files').eq('order_ref', ref).execute().data
        remote = f'orders/{ref}/final_books/adventure_{index:02d}/book_{index:02d}.pdf'
        if len(rows or []) != 1 or rows[0]['status'] != 'BOOKS_READY' or remote not in (rows[0]['generated_files'] or []):
            raise ValueError(f'Livre non terminé ou sauvegarde non déclarée : {ref}.')
        data = db.storage.from_(BUCKET).download(remote)
        if not data.startswith(b'%PDF-') or b'%%EOF' not in data[-1024:]:
            raise ValueError(f'Sauvegarde PDF illisible : {ref}.')
        path = root / ref / 'final_books' / f'adventure_{index:02d}'
        if path.is_symlink():
            raise ValueError('Un lien symbolique ne peut pas être nettoyé.')
        resolved = path.resolve()
        if not resolved.is_relative_to(root) or resolved != path:
            raise ValueError('Chemin hors du répertoire de travail.')
        if path.exists() and any(p.is_symlink() for p in path.rglob('*')):
            raise ValueError('Lien symbolique dans les fichiers du livre.')
        size = sum(p.stat().st_size for p in path.rglob('*') if p.is_file()) if path.exists() else 0
        targets.append((ref, path, size, hashlib.sha256(data).hexdigest()))
        logging.info('STORAGE_CLEANUP sauvegarde vérifiée %s : %d octets ; cache local %d octets', remote, len(data), size)
    before = shutil.disk_usage(root).free
    removed = []
    for ref, path, size, digest in targets:
        # Recheck status immediately before deletion; never clean a resumed order.
        rows = db.table('orders').select('status').eq('order_ref', ref).execute().data
        if len(rows or []) != 1 or rows[0]['status'] != 'BOOKS_READY':
            raise ValueError('La commande a changé de statut pendant le nettoyage.')
        if path.exists():
            shutil.rmtree(path)
        removed.append(dict(order_ref=ref, path=str(path), local_bytes=size, remote_pdf_sha256=digest))
    result = dict(books=removed, free_before=before, free_after=shutil.disk_usage(root).free)
    receipt.write_text(json.dumps(result), encoding='utf-8')
    logging.info('STORAGE_CLEANUP terminé : %s', json.dumps(result))
    return result
