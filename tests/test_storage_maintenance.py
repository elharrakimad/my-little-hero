import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from storage_maintenance import cleanup_completed_books


class StorageMaintenanceTests(unittest.TestCase):
    def setup_plan(self, root):
        plan = [dict(order_ref=f'MLH-20261101-00000{i}-ABCDEF', index=1) for i in range(5)]
        rows = {}
        for item in plan:
            ref = item['order_ref']
            path = root/ref/'final_books'/'adventure_01'
            path.mkdir(parents=True)
            (path/'page.png').write_bytes(b'cached illustration')
            (root/ref/'reference.png').write_bytes(b'keep original')
            rows[ref] = dict(status='BOOKS_READY', generated_files=[f'orders/{ref}/final_books/adventure_01/book_01.pdf'])
        protected = root/'interrupted'/'page_08.png'
        protected.parent.mkdir()
        protected.write_bytes(b'keep interruption')
        db = MagicMock()
        query = db.table.return_value
        query.select.return_value = query
        current = {}
        def eq(key, value):
            current['ref'] = value
            return query
        query.eq.side_effect = eq
        query.execute.side_effect = lambda: SimpleNamespace(data=[rows[current['ref']]])
        db.storage.from_.return_value.download.return_value = b'%PDF-1.4\nbackup\n%%EOF'
        return plan, db, rows, protected

    def test_only_five_explicit_book_caches_are_removed_and_operation_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plan, db, _, protected = self.setup_plan(root)
            result = cleanup_completed_books(db, root, json.dumps(plan))
            self.assertEqual(len(result['books']), 5)
            self.assertTrue(protected.exists())
            for item in plan:
                self.assertFalse((root/item['order_ref']/'final_books'/'adventure_01').exists())
                self.assertTrue((root/item['order_ref']/'reference.png').exists())
            self.assertEqual(db.storage.from_.return_value.download.call_count, 5)
            cleanup_completed_books(db, root, json.dumps(plan))
            self.assertEqual(db.storage.from_.return_value.download.call_count, 5)
            db.table.return_value.update.assert_not_called()

    def test_a_single_bad_backup_or_unfinished_order_prevents_all_deletions(self):
        for bad in ('backup', 'status'):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                plan, db, rows, _ = self.setup_plan(root)
                if bad == 'backup':
                    db.storage.from_.return_value.download.side_effect = [b'%PDF-1.4\n%%EOF']*4 + [b'truncated']
                else:
                    rows[plan[-1]['order_ref']]['status'] = 'GENERATION_INTERRUPTED'
                with self.assertRaises(ValueError):
                    cleanup_completed_books(db, root, json.dumps(plan))
                for item in plan:
                    self.assertTrue((root/item['order_ref']/'final_books'/'adventure_01'/'page.png').exists())

    def test_outside_paths_and_more_than_five_books_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plan, db, _, _ = self.setup_plan(root)
            for invalid in (plan+[plan[0]], [dict(order_ref='../other', index=1)]):
                with self.assertRaises(ValueError):
                    cleanup_completed_books(db, root, json.dumps(invalid))
