from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from generation_worker import process_once, recover_job, save_journal, generate_isolated, run_maintenance
from order_actions import ProductionStopped


class Database:
    def __init__(self, rows):
        self.rows = rows
        self.claim_race = False
        self.claim_error = False

    def table(self, _):
        return Query(self)


class Query:
    def __init__(self, db):
        self.db, self.filters, self.values = db, {}, None

    def select(self, _): return self
    def order(self, _): return self
    def limit(self, _): return self
    def eq(self, key, value):
        self.filters[key] = value
        return self

    def update(self, values):
        self.values = values
        return self

    def execute(self):
        if self.values == {"status": "GENERATING"}:
            if self.db.claim_error:
                raise ConnectionError("ambiguous claim")
            if self.db.claim_race:
                self.db.rows[0]["status"] = "GENERATING"
        rows = [r for r in self.db.rows if all(r.get(k) == v for k, v in self.filters.items())]
        if self.values:
            for row in rows: row.update(self.values)
        return SimpleNamespace(data=[dict(row) for row in rows])


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.journal = Path(self.temp.name) / "active_job.json"
        self.db = Database([{"order_ref": "ONE", "status": "PAID"}])
        self.normalizer = patch("generation_worker.normalize_order", lambda row: row)
        self.normalizer.start()
        self.addCleanup(self.normalizer.stop)

    def test_unpaid_orders_never_generate(self):
        self.db.rows[0]["status"] = "WAITING_FOR_PAYMENT"
        self.assertFalse(process_once(self.db, self.journal, lambda _: self.fail("unpaid")))

    def test_success_runs_without_browser_and_clears_journal(self):
        def generate(order):
            self.assertEqual(order["status"], "GENERATING")
            self.db.rows[0]["status"] = "BOOKS_READY"
        self.assertTrue(process_once(self.db, self.journal, generate))
        self.assertEqual(self.db.rows[0]["status"], "BOOKS_READY")
        self.assertFalse(self.journal.exists())

    def test_lost_claim_does_not_generate(self):
        self.db.claim_race = True
        self.assertFalse(process_once(self.db, self.journal, lambda _: self.fail("duplicate")))

    def test_failure_requires_owner_retry(self):
        def generate(_): raise ValueError("AI failure")
        with self.assertLogs(level="ERROR"):
            process_once(self.db, self.journal, generate)
        self.assertEqual(self.db.rows[0]["status"], "GENERATION_INTERRUPTED")
        self.assertFalse(process_once(self.db, self.journal, lambda _: self.fail("retry loop")))

    def test_restart_recovers_only_journaled_job(self):
        self.db.rows[0]["status"] = "GENERATING"
        self.db.rows.append({"order_ref": "OTHER", "status": "GENERATING"})
        save_journal(self.journal, "ONE")
        recover_job(self.db, self.journal)
        self.assertEqual([r["status"] for r in self.db.rows], ["PAID", "GENERATING"])

    def test_uncertain_claim_preserves_recovery_journal(self):
        self.db.claim_error = True
        with self.assertRaises(ConnectionError):
            process_once(self.db, self.journal, lambda _: None)
        self.assertTrue(self.journal.exists())

    def test_isolated_generation_waits_and_reports_failure_without_automatic_ai_retry(self):
        for code in (0, 2, -9):
            with self.subTest(code=code), patch('generation_worker.subprocess.run', return_value=SimpleNamespace(returncode=code)) as run:
                if code == 0:
                    generate_isolated({'order_ref': 'ONE'})
                elif code == 2:
                    with self.assertRaises(ProductionStopped): generate_isolated({'order_ref': 'ONE'})
                else:
                    with self.assertRaises(RuntimeError): generate_isolated({'order_ref': 'ONE'})
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[0][-1], 'ONE')

    def test_maintenance_outage_does_not_break_worker(self):
        with patch('storage_maintenance.cleanup_delivered_books', side_effect=ConnectionError('offline')), self.assertLogs(level='ERROR'):
            run_maintenance(self.db, self.journal.parent)

    def test_queue_parent_does_not_load_image_or_ai_engine(self):
        import subprocess
        import sys
        result = subprocess.run([sys.executable, '-c',
            'import generation_worker, sys; '
            'assert "book_layout" not in sys.modules; '
            'assert "generate_book" not in sys.modules; '
            'assert "openai" not in sys.modules'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_maintenance_can_be_disabled(self):
        with patch.dict('os.environ', {'MLH_AUTO_CLEANUP': '0'}), patch('storage_maintenance.cleanup_delivered_books') as cleanup:
            run_maintenance(self.db, self.journal.parent)
            cleanup.assert_not_called()

    def test_child_progress_is_preserved_on_failure(self):
        def failed(order):
            self.db.rows[0]['generation_progress'] = {'stage': 'illustrations', 'page_index': 8, 'percent': 70}
            raise RuntimeError('child stopped')
        with self.assertLogs(level='ERROR'):
            process_once(self.db, self.journal, failed)
        self.assertEqual(self.db.rows[0]['generation_progress']['failed_stage'], 'illustrations')
        self.assertEqual(self.db.rows[0]['generation_progress']['page_index'], 8)


if __name__ == "__main__":
    unittest.main()
