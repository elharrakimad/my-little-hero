import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from storage_maintenance import cleanup_completed_books, cleanup_delivered_books, verify_private_pdf


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

    def test_auto_cleanup_only_delivered_and_never_originals_or_remote_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plan, db, rows, protected = self.setup_plan(root)
            rows[plan[0]['order_ref']]['status'] = 'DELIVERED'
            rows[plan[1]['order_ref']]['status'] = 'SHIPPED'
            rows[plan[2]['order_ref']]['status'] = 'GENERATING'
            checked = []
            def verify(remote):
                checked.append(remote)
                return {'bytes': 100, 'sha256': 'verified', 'pages': 12}
            result = cleanup_delivered_books(db, root, verify=verify)
            self.assertEqual(len(result['books']), 1)
            self.assertEqual(len(checked), 1)
            self.assertFalse((root/plan[0]['order_ref']/'final_books'/'adventure_01').exists())
            self.assertTrue((root/plan[0]['order_ref']/'reference.png').exists())
            for item in plan[1:]:
                self.assertTrue((root/item['order_ref']/'final_books'/'adventure_01').exists())
            self.assertTrue(protected.exists())
            self.assertEqual(cleanup_delivered_books(db, root, verify=verify)['books'], [])
            db.table.return_value.update.assert_not_called()
            db.storage.from_.assert_not_called()

    def test_auto_cleanup_failure_preserves_entire_batch_and_dry_run_never_removes(self):
        for mode in ('dry', 'bad_backup', 'active'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                plan, db, rows, _ = self.setup_plan(root)
                for row in rows.values(): row['status'] = 'DELIVERED'
                verify = MagicMock(return_value={'bytes': 100, 'pages': 12, 'sha256': 'ok'})
                if mode == 'active': (root/'active_job.json').write_text('{}')
                if mode == 'bad_backup':
                    verify.side_effect = [{'bytes': 100}] * 4 + [ValueError('bad PDF')]
                    with self.assertRaises(ValueError): cleanup_delivered_books(db, root, verify=verify)
                else:
                    cleanup_delivered_books(db, root, verify=verify, dry_run=mode == 'dry')
                for item in plan:
                    self.assertTrue((root/item['order_ref']/'final_books'/'adventure_01').exists())
                if mode == 'active': verify.assert_not_called()

    def test_changed_status_and_unsafe_paths_block_deletion(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plan, db, rows, _ = self.setup_plan(root)
            row = rows[plan[0]['order_ref']]
            row['status'] = 'DELIVERED'
            def verify(remote):
                row['status'] = 'GENERATING'
                return {'sha256': 'ok'}
            with self.assertRaises(ValueError): cleanup_delivered_books(db, root, verify=verify)
            self.assertTrue((root/plan[0]['order_ref']/'final_books'/'adventure_01').exists())
            from storage_maintenance import _cache_path
            with self.assertRaises(ValueError): _cache_path(root, '../outside', 1)

    def test_streamed_verification_parses_pdf_and_rejects_truncation(self):
        import io
        from unittest.mock import patch
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        content = io.BytesIO()
        writer.write(content)
        data = content.getvalue()
        class Response(io.BytesIO):
            def read(self, size=-1):
                self.assert_bounded(size)
                return super().read(size)
            def assert_bounded(self, size):
                if size != 65536: raise AssertionError('unbounded download')
        with patch.dict('os.environ', {'SUPABASE_URL': 'https://example.com', 'SUPABASE_SECRET_KEY': 'test'}):
            with patch('urllib.request.urlopen', return_value=Response(data)):
                self.assertEqual(verify_private_pdf('orders/test.pdf')['pages'], 1)
            with patch('urllib.request.urlopen', return_value=Response(data[:-20])):
                with self.assertRaises(ValueError): verify_private_pdf('orders/test.pdf')
