import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from repair_paired_book import repair


class PairedRepairTests(unittest.TestCase):
    def test_repair_publishes_a_new_file_and_preserves_color_and_previous_coloring(self):
        self.check_repair()

    def test_failed_verification_never_changes_downloads_or_order_status(self):
        self.check_repair(fail=True)

    def check_repair(self, fail=False):
        ref = 'MLH-20261112-012523-D99494'
        prefix = f'orders/{ref}/final_books/'
        old_files = [prefix+'adventure_01/book_01.pdf', prefix+'adventure_02/book_02.pdf']
        first = dict(title='Same story', theme='Science', idea='', book_style='colored')
        second = dict(first, book_style='coloring', paired_version='same-scenes-v1', image_only=True, shared_story_from=1)
        row = dict(order_ref=ref, status='BOOKS_READY', pack='Super Héros',
                   adventures=[first, second], generated_files=old_files)
        db = MagicMock()
        query = db.table.return_value
        query.select.return_value = query
        query.eq.return_value = query
        query.update.return_value = query
        query.execute.side_effect = [SimpleNamespace(data=[row]),
            SimpleNamespace(data=[dict(status=row['status'], generated_files=old_files)]),
            SimpleNamespace(data=[{'id': 'saved'}])]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_pdf = root/ref/'final_books/adventure_02/book_02.pdf'
            old_pdf.parent.mkdir(parents=True)
            old_pdf.write_bytes(b'previous coloring')
            def build(source, target, pdf, **kwargs):
                target.mkdir(parents=True, exist_ok=True)
                pdf.write_bytes(b'clean new PDF')
                return pdf
            verified = MagicMock(return_value={'pages': 10, 'sha256': 'verified'})
            if fail: verified.side_effect = ValueError('backup verification failed')
            with patch.dict(os.environ, {'MLH_WORK_DIR': str(root)}), \
                 patch.dict('sys.modules', {'fcntl': SimpleNamespace(flock=MagicMock(), LOCK_EX=1, LOCK_NB=2)}), \
                 patch('order_production.get_supabase_client', return_value=db), \
                 patch('order_production.normalize_order', side_effect=lambda row: row), \
                 patch('order_production.storage_upload') as upload, \
                 patch('paired_books.build_paired_coloring', side_effect=build), \
                 patch('storage_maintenance.verify_private_pdf', verified):
                if fail:
                    with self.assertRaises(ValueError): repair(ref, publish=True)
                    query.update.assert_not_called()
                else:
                    result = repair(ref, publish=True)
                    self.assertTrue(result['color_pdf_unchanged'])
                    self.assertTrue(result['previous_coloring_pdf_preserved'])
                    saved = query.update.call_args.args[0]
                    self.assertEqual(saved['generated_files'][0], old_files[0])
                    self.assertTrue(saved['generated_files'][1].endswith('book_02_clean_v2.pdf'))
                    self.assertEqual(set(saved), {'generated_files'})
                upload.assert_called_once()
            self.assertEqual(old_pdf.read_bytes(), b'previous coloring')
            self.assertFalse(list(root.glob('repair_*.lock')))
