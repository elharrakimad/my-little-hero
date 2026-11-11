"""Single-instance durable worker. Run on one Render worker with a persistent disk."""
import json
import logging
import os
from pathlib import Path
import signal
import threading
import subprocess
import sys
import time

from order_production import get_supabase_client, normalize_order
from production_status import failed_progress
from order_actions import ProductionStopped


def generate_isolated(order):
    """Release all image/SDK/PDF memory after each order, including failures."""
    result = subprocess.run([sys.executable, '-u', str(Path(__file__).with_name('production_job.py')),
                             order['order_ref']], check=False)
    if result.returncode == 2:
        raise ProductionStopped('Production arrêtée dans le processus de génération.')
    if result.returncode:
        raise RuntimeError(f'Processus de génération interrompu (code {result.returncode}). '
                           'Fichiers conservés ; reprise manuelle depuis Admin.')


def run_maintenance(db, directory):
    # A Storage outage must not bring down order processing or delete a cache.
    try:
        if os.getenv('MLH_AUTO_CLEANUP', '1') != '1':
            return
        from storage_maintenance import cleanup_delivered_books
        cleanup_delivered_books(db, directory, max_books=50)
    except Exception:
        logging.exception('AUTO_CLEANUP différé : vérification impossible, caches conservés.')


def save_journal(path, order_ref):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"order_ref": order_ref}), encoding="utf-8")
    temporary.replace(path)


def recover_job(db, journal):
    """Only recover this worker's journal, never other in-flight orders."""
    if not journal.exists():
        return
    order_ref = json.loads(journal.read_text(encoding="utf-8"))["order_ref"]
    (db.table("orders").update({"status": "PAID"})
        .eq("order_ref", order_ref).eq("status", "GENERATING").execute())
    journal.unlink()


def process_once(db, journal, generate):
    rows = (db.table("orders").select("*").eq("status", "PAID")
        .order("created_at").limit(1).execute()).data or []
    if not rows:
        return False
    candidate = rows[0]
    # Write before claiming: a crash after the database update remains recoverable.
    save_journal(journal, candidate["order_ref"])
    claimed = (db.table("orders").update({"status": "GENERATING"})
        .eq("order_ref", candidate["order_ref"]).eq("status", "PAID").execute()).data or []
    if not claimed:
        journal.unlink()
        return False
    order = normalize_order(claimed[0])
    try:
        generate(order)
    except ProductionStopped:
        logging.info("Production arrêtée pour %s ; commande et fichiers conservés.", order["order_ref"])
    except Exception as exc:
        logging.exception("Production interrompue pour %s", order["order_ref"])
        # The isolated child persisted more recent page progress than the parent.
        latest = (db.table('orders').select('generation_progress')
                  .eq('order_ref', order['order_ref']).execute()).data or []
        if latest and latest[0].get('generation_progress'):
            order['generation_progress'] = latest[0]['generation_progress']
        # Do not automatically retry costly AI failures. The owner can requeue in Admin.
        (db.table("orders").update({"status": "GENERATION_INTERRUPTED",
            "generation_progress": failed_progress(order, exc)})
            .eq("order_ref", order["order_ref"]).eq("status", "GENERATING").execute())
    journal.unlink()
    return True


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise RuntimeError("OPENAI_API_KEY est requis sur le worker.")
    directory = Path(os.environ["MLH_WORK_DIR"]).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    # Render's disk is exclusive to one instance. Also prevent two processes using it.
    import fcntl
    with (directory / "worker.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        db = get_supabase_client()
        maintenance = os.getenv('MLH_CLEANUP_PLAN', '').strip()
        if maintenance:
            from storage_maintenance import cleanup_completed_books
            cleanup_completed_books(db, directory, maintenance)
        journal = directory / "active_job.json"
        recover_job(db, journal)
        stopping = threading.Event()
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda *_: stopping.set())
        logging.info("Worker prêt. Surveillance des commandes dont le paiement est validé.")
        logging.info('Génération isolée ; nettoyage automatique des caches DELIVERED toutes les 5 minutes à vide.')
        next_cleanup = 0
        while not stopping.is_set():
            # Infrastructure/claim errors exit the process, retaining the journal.
            # Render restarts it; resume uses existing story, images and PDFs.
            worked = process_once(db, journal, generate_isolated)
            if not worked:
                if time.monotonic() >= next_cleanup:
                    run_maintenance(db, directory)
                    next_cleanup = time.monotonic() + 300
                stopping.wait(10)


if __name__ == "__main__":
    main()
