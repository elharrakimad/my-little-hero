from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from order_actions import cancel_order, save_production_fields, ProductionStopped
from generation_worker import process_once, recover_job, save_journal
from test_generation_worker import Database


class CancellationTests(unittest.TestCase):
    def test_cancel_preserves_files_and_does_not_touch_other_orders(self):
        for status in ("WAITING_FOR_PAYMENT", "PAID", "GENERATING", "GENERATION_INTERRUPTED", "BOOKS_READY"):
            db = Database([{"order_ref": "ONE", "status": status, "generated_files": ["book.pdf"]},
                {"order_ref": "OTHER", "status": status}])
            self.assertTrue(cancel_order(db, "ONE", status))
            self.assertEqual(db.rows[0]["status"], "CANCELLED")
            self.assertEqual(db.rows[0]["generated_files"], ["book.pdf"])
            self.assertEqual(db.rows[1]["status"], status)

    def test_stale_confirmation_and_repeat_cancellation_do_not_change_order(self):
        db = Database([{"order_ref": "ONE", "status": "GENERATING"}])
        self.assertFalse(cancel_order(db, "ONE", "PAID"))
        self.assertTrue(cancel_order(db, "ONE", "GENERATING"))
        self.assertFalse(cancel_order(db, "ONE", "CANCELLED"))

    def test_late_progress_or_completion_cannot_revive_cancelled_order(self):
        db = Database([{"order_ref": "ONE", "status": "CANCELLED"}])
        for fields in ({"generation_progress": {"stage": "illustrations"}},
                {"status": "GENERATING", "generated_files": ["late.pdf"]},
                {"status": "BOOKS_READY"}, {"generation_progress": {"stage": "complete"}}):
            with self.assertRaises(ProductionStopped):
                save_production_fields(db, "ONE", fields)
            self.assertEqual(db.rows[0], {"order_ref": "ONE", "status": "CANCELLED"})

    def test_successful_production_still_saves_final_progress(self):
        db = Database([{"order_ref": "ONE", "status": "GENERATING"}])
        save_production_fields(db, "ONE", {"status": "BOOKS_READY"})
        save_production_fields(db, "ONE", {"generation_progress": {"stage": "complete"}})
        self.assertEqual(db.rows[0]["generation_progress"]["stage"], "complete")

    def test_worker_stops_at_checkpoint_and_restart_never_requeues_cancellation(self):
        db = Database([{"order_ref": "ONE", "status": "PAID"}])
        with tempfile.TemporaryDirectory() as folder, patch("generation_worker.normalize_order", lambda row: row):
            journal = Path(folder) / "job.json"
            def generate(order):
                cancel_order(db, order["order_ref"], "GENERATING")
                save_production_fields(db, order["order_ref"], {"generation_progress": {"stage": "illustrations"}})
                self.fail("A cancelled job must stop before the next AI request")
            process_once(db, journal, generate)
            self.assertEqual(db.rows[0]["status"], "CANCELLED")
            self.assertFalse(journal.exists())
            save_journal(journal, "ONE")
            recover_job(db, journal)
            self.assertFalse(process_once(db, journal, lambda _: self.fail("Cancelled order generated")))
            self.assertEqual(db.rows[0]["status"], "CANCELLED")
