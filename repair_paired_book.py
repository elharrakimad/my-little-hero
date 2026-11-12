"""Explicit repair of one completed paired coloring book; preserve the color PDF."""
import argparse
import json
import os
from pathlib import Path
import re


def repair(order_ref, *, review_page=None, publish=False):
    from order_production import get_supabase_client, normalize_order, storage_upload
    from paired_books import build_paired_coloring, is_paired_coloring, RENDER_VERSION
    from storage_maintenance import verify_private_pdf
    if not re.fullmatch(r'MLH-[0-9]{8}-[0-9]{6}-[A-F0-9]{6}', order_ref):
        raise ValueError('Référence invalide.')
    if review_page is not None and publish:
        raise ValueError('Un contrôle de page ne publie pas de PDF.')
    db = get_supabase_client()
    rows = db.table('orders').select('*').eq('order_ref', order_ref).execute().data
    if len(rows or []) != 1 or rows[0]['status'] not in {'BOOKS_READY', 'SHIPPED', 'DELIVERED'}:
        raise ValueError('Réparation réservée à une commande terminée précise.')
    row = rows[0]
    order = normalize_order(row)
    if len(order['adventures']) != 2 or not is_paired_coloring(order, 2, order['adventures'][1]):
        raise ValueError('Cette commande ne possède pas de cahier lié.')
    root = Path(os.environ['MLH_WORK_DIR']).resolve(strict=True)
    import fcntl
    gate = (root/'production_gate.lock').open('a')
    try:
        fcntl.flock(gate, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BaseException:
        gate.close()
        raise
    lock = root/f'repair_{order_ref}.lock'
    try:
        with lock.open('x') as file:
            file.write('Clean lineart repair; preserve originals and remote PDFs.\n')
        if (root/'active_job.json').exists():
            raise ValueError('Une production est active ; réessayer à vide.')
        directory = root/order_ref/'final_books'
        source = directory/'adventure_01'/'colored'
        target = directory/'adventure_02'/RENDER_VERSION
        target_pdf = target/'book_02_clean_v2.pdf'
        result = build_paired_coloring(source, target, target_pdf, review_page=review_page)
        if not publish:
            return {'local_file': str(result), 'published': False}
        old_files = list(row.get('generated_files') or [])
        marker = '/adventure_02/'
        if len([p for p in old_files if marker in p]) != 1:
            raise ValueError('Liste de fichiers ambiguë ; rien ne sera remplacé.')
        remote = f'orders/{order_ref}/final_books/adventure_02/book_02_clean_v2.pdf'
        storage_upload(db, remote, result, 'application/pdf')
        verified = verify_private_pdf(remote)
        if verified['pages'] != 10:
            raise ValueError('Le cahier vérifié ne contient pas dix pages.')
        latest = db.table('orders').select('status,generated_files').eq('order_ref', order_ref).execute().data
        if (len(latest or []) != 1 or latest[0]['status'] != row['status']
                or latest[0]['generated_files'] != old_files):
            raise ValueError('La commande a changé ; PDF original toujours référencé.')
        new_files = [remote if marker in p else p for p in old_files]
        changed = (db.table('orders').update({'generated_files': new_files})
                   .eq('order_ref', order_ref).eq('status', row['status']).execute()).data
        if not changed:
            raise ValueError('Mise à jour non appliquée ; PDF original conservé.')
        receipt = {'order_ref': order_ref, 'previous_files': old_files,
                   'generated_files': new_files, 'verified': verified}
        (target/'repair_receipt.json').write_text(json.dumps(receipt), encoding='utf-8')
        return {'published': True, 'pages': verified['pages'], 'color_pdf_unchanged': new_files[0] == old_files[0],
                'previous_coloring_pdf_preserved': True, 'remote_file': remote}
    finally:
        lock.unlink(missing_ok=True)
        gate.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('order_ref')
    parser.add_argument('--review-page', type=int)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    print(json.dumps(repair(args.order_ref, review_page=args.review_page, publish=args.publish)), flush=True)
