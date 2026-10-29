from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from production_status import ProgressTracker, failed_progress, progress_percent, safe_error
import order_production


class ProductionStatusTests(unittest.TestCase):
    def test_page_progress_and_multiple_books(self):
        self.assertLess(progress_percent("illustrations", page_index=1), progress_percent("illustrations", page_index=9))
        self.assertLess(progress_percent("upload", book_index=1, book_total=3), 34)
        self.assertEqual(progress_percent("complete", book_total=3), 100)

    def test_error_preserves_stage_and_masks_credentials(self):
        order = {"generation_progress": {"stage": "upload", "percent": 96}}
        progress = failed_progress(order, "InvalidKey sk-1234567890-secret Bearer abcde")
        self.assertEqual(progress["failed_stage"], "upload")
        self.assertEqual(progress["percent"], 96)
        self.assertNotIn("sk-123", progress["error"])
        self.assertNotIn("abcde", progress["error"])

    def test_history_is_bounded_and_updates_saved(self):
        order, saved = {}, []
        report = ProgressTracker(order, saved.append)
        for i in range(90):
            report("illustrations", str(i), page_index=1)
        self.assertEqual(len(order["generation_progress"]["history"]), 80)
        self.assertEqual(len(saved), 90)
        self.assertEqual(order["generation_progress"]["error"], None)

    def test_accented_pdf_is_uploaded_using_safe_key_without_regeneration(self):
        with tempfile.TemporaryDirectory() as directory:
            title = "Itar et le panier décisif"
            folder = Path(directory) / "final_books" / "adventure_01"
            folder.mkdir(parents=True)
            pdf = folder / "Itar_Itar_et_le_panier_décisif.pdf"
            pdf.write_bytes(b"existing PDF")
            order = {"order_ref": "TEST", "child_name": "Itar", "age": 11, "language": "Français",
                "adventures": [{"title": title, "theme": "Basket"}], "generated_files": [], "_dir": Path(directory)}
            book_engine = MagicMock()
            uploads, updates = [], []
            with patch.dict("sys.modules", {"book_engine": book_engine}), \
                patch.object(order_production, "get_supabase_client", return_value=MagicMock()), \
                patch.object(order_production, "ensure_order_assets", return_value=(Path("reference.png"), [Path("cover.png")])), \
                patch.object(order_production, "storage_upload", side_effect=lambda db, path, *args: uploads.append(path)), \
                patch.object(order_production, "update_order_fields", side_effect=lambda ref, fields: updates.append(fields)):
                result = order_production.generate_order(order)
            book_engine.generate_book_from_adventure.assert_not_called()
            self.assertEqual(uploads, ["orders/TEST/final_books/adventure_01/book_01.pdf"])
            self.assertTrue(uploads[0].isascii())
            self.assertEqual(order["status"], "BOOKS_READY")
            self.assertEqual(order["generation_progress"]["percent"], 100)
            self.assertEqual(result, uploads)


if __name__ == "__main__":
    unittest.main()
