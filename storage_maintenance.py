"""Explicit, bounded removal of local caches after verifying private PDF backups."""
import hashlib
import json
import logging
from pathlib import Path
import re
import shutil
import os
import tempfile
import urllib.request
from urllib.parse import quote

BUCKET = 'my-little-hero-files'


def verify_private_pdf(remote):
    """Stream the private backup to ephemeral disk, then parse every page.

    No signed URL, credential or PDF bytes are logged. Memory is bounded during
    transfer; originals in Storage are never modified.
    """
    from pypdf import PdfReader
    url = os.environ['SUPABASE_URL'].rstrip('/')
    key = os.getenv('SUPABASE_SECRET_KEY') or os.environ['SUPABASE_SERVICE_KEY']
    request = urllib.request.Request(
        url + '/storage/v1/object/authenticated/' + BUCKET + '/' + quote(remote, safe='/'),
        headers={'apikey': key, 'Authorization': 'Bearer ' + key})
    digest, size = hashlib.sha256(), 0
    with tempfile.TemporaryFile() as file:
        with urllib.request.urlopen(request, timeout=60) as response:
            while chunk := response.read(64 * 1024):
                size += len(chunk)
                if size > 64 * 1024 * 1024:
                    raise ValueError('PDF trop volumineux pour la vérification automatique.')
                file.write(chunk)
                digest.update(chunk)
        file.seek(0)
        if file.read(5) != b'%PDF-':
            raise ValueError('Sauvegarde non PDF.')
        file.seek(max(0, size - 1024))
        if b'%%EOF' not in file.read():
            raise ValueError('Sauvegarde PDF incomplète.')
        file.seek(0)
        reader = PdfReader(file, strict=True)
        if reader.is_encrypted or not len(reader.pages):
            raise ValueError('Sauvegarde PDF protégée ou vide.')
        for page in reader.pages:
            if page.get_contents() is not None:
                page.get_contents().get_data()
        return {'bytes': size, 'sha256': digest.hexdigest(), 'pages': len(reader.pages)}


def _cache_path(root, ref, index):
    if not re.fullmatch(r'MLH-[0-9]{8}-[0-9]{6}-[A-F0-9]{6}', ref):
        raise ValueError('Référence invalide.')
    if type(index) is not int or not 1 <= index <= 3:
        raise ValueError('Numéro de livre invalide.')
    path = root / ref / 'final_books' / f'adventure_{index:02d}'
    if path.is_symlink() or path.resolve() != path or not path.resolve().is_relative_to(root):
        raise ValueError('Chemin de cache non sûr.')
    if path.exists() and any(p.is_symlink() for p in path.rglob('*')):
        raise ValueError('Lien symbolique dans le cache.')
    return path


def cleanup_delivered_books(db, root, *, max_books=5, verify=verify_private_pdf, dry_run=False):
    """Only delivered orders; never infer that a browser download completed.

    Verify the entire bounded batch before deleting anything. Recheck status
    immediately before each removal. Leave all originals outside final_books,
    all database rows and all remote files intact.
    """
    root = Path(root).resolve(strict=True)
    if not 1 <= max_books <= 50:
        raise ValueError('Lot de nettoyage invalide.')
    if (root / 'active_job.json').exists():
        logging.info('AUTO_CLEANUP différé : production active ou récupération nécessaire.')
        return {'books': [], 'deferred': True}
    targets = []
    for order_dir in sorted(root.glob('MLH-*')):
        ref = order_dir.name
        if not re.fullmatch(r'MLH-[0-9]{8}-[0-9]{6}-[A-F0-9]{6}', ref):
            continue
        # Most already cleaned orders can be skipped without any network call.
        paths = [_cache_path(root, ref, i) for i in range(1, 4)]
        if not any(p.is_dir() and any(p.iterdir()) for p in paths):
            continue
        rows = db.table('orders').select('status,generated_files').eq('order_ref', ref).execute().data
        if len(rows or []) != 1 or rows[0]['status'] != 'DELIVERED':
            continue
        for index, path in enumerate(paths, 1):
            if not path.is_dir() or not any(path.iterdir()):
                continue
            remote = f'orders/{ref}/final_books/adventure_{index:02d}/book_{index:02d}.pdf'
            if remote not in (rows[0].get('generated_files') or []):
                raise ValueError(f'Sauvegarde non déclarée : {ref}, livre {index}.')
            backup = verify(remote)
            size = sum(p.stat().st_size for p in path.rglob('*') if p.is_file())
            targets.append(dict(order_ref=ref, index=index, local_bytes=size, backup=backup))
            if len(targets) == max_books:
                break
        if len(targets) == max_books:
            break
    before = shutil.disk_usage(root).free
    removed = []
    for item in targets:
        if not dry_run:
            if (root / 'active_job.json').exists():
                raise ValueError('Production démarrée pendant le nettoyage.')
            rows = db.table('orders').select('status').eq('order_ref', item['order_ref']).execute().data
            if len(rows or []) != 1 or rows[0]['status'] != 'DELIVERED':
                raise ValueError('La commande a changé de statut.')
            path = _cache_path(root, item['order_ref'], item['index'])
            shutil.rmtree(path)
        removed.append(item)
    result = dict(books=removed, dry_run=dry_run, free_before=before,
                  free_after=shutil.disk_usage(root).free)
    if removed and not dry_run:
        temporary = root / 'auto_cleanup_latest.tmp'
        temporary.write_text(json.dumps(result), encoding='utf-8')
        temporary.replace(root / 'auto_cleanup_latest.json')
        logging.info('AUTO_CLEANUP terminé : %d livres, %d octets libérés, PDF privés conservés.',
                     len(removed), result['free_after'] - before)
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Caches des commandes livrées uniquement.')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--max-books', type=int, default=5)
    args = parser.parse_args()
    from order_production import get_supabase_client
    print(json.dumps(cleanup_delivered_books(get_supabase_client(), os.environ['MLH_WORK_DIR'],
        max_books=args.max_books, dry_run=not args.apply)))


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
