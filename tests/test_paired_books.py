import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from paired_books import build_paired_coloring, is_paired_coloring, PAIR_VERSION

ROOT = Path(__file__).resolve().parents[1]


def source_book(folder):
    from PIL import Image
    folder = Path(folder)
    (folder/'pages').mkdir(parents=True)
    story = '\n'.join(f'PAGE {i}\nTitre : Aventure {i}\nTexte : Adam aide ses amis.\nScène à illustrer : Adam dans la forêt.' for i in range(1, 11))
    (folder/'story.txt').write_text(story, encoding='utf-8')
    for i in range(1, 11):
        with Image.open(ROOT/'examples/itar/story-illustration-v2.png') as image:
            image.save(folder/'pages'/f'page_{i:02d}.png')
    return folder


class PairedBooksTests(unittest.TestCase):
    def test_ten_full_bleed_images_without_any_visible_text_or_extra_pages(self):
        import pdfplumber
        from PIL import Image
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = source_book(root/'source')
            before = hashlib.sha256((source/'pages/page_01.png').read_bytes()).hexdigest()
            output = root/'coloring'
            pdf = build_paired_coloring(source, output, output/'same_story.pdf')
            self.assertEqual((source/'story.txt').read_bytes(), (output/'story.txt').read_bytes())
            self.assertEqual(before, hashlib.sha256((source/'pages/page_01.png').read_bytes()).hexdigest())
            self.assertEqual(len(PdfReader(pdf).pages), 10)
            with pdfplumber.open(pdf) as document:
                for page in document.pages:
                    self.assertFalse(page.extract_text())
                    image = page.images[0]
                    self.assertLessEqual(image['x0'], .01)
                    self.assertGreaterEqual(image['x1'], page.width-.01)
                    self.assertLessEqual(image['top'], .01)
                    self.assertGreaterEqual(image['bottom'], page.height-.01)
            with Image.open(output/'pages/page_01.png') as image:
                self.assertEqual({value for _, value in image.getcolors()}, {0, 255})
                with Image.open(source/'pages/page_01.png') as original:
                    self.assertEqual(image.size, original.size)
            # Resume reuses existing conversions, without AI or a different scene.
            with patch('paired_books.color_to_lineart') as convert:
                build_paired_coloring(source, output, pdf)
                convert.assert_not_called()

    def test_missing_color_scene_fails_without_creating_a_different_story(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = source_book(root/'source')
            (source/'pages/page_04.png').unlink()
            with self.assertRaises(FileNotFoundError):
                build_paired_coloring(source, root/'out', root/'out/book.pdf')
            self.assertFalse((root/'out/book.pdf').exists())

    def test_pairing_is_restricted_to_new_bundle_orders(self):
        first = dict(title='Same title', theme='Science', idea='', book_style='colored')
        second = dict(first, book_style='coloring', paired_version=PAIR_VERSION,
                      image_only=True, shared_story_from=1)
        for pack in ('Super Héros', 'Ultimate Hero'):
            self.assertTrue(is_paired_coloring({'pack': pack, 'adventures': [first, second]}, 2, second))
        for pack in ('Digital', 'Petit Artiste', 'Mon Histoire'):
            with self.assertRaises(ValueError):
                is_paired_coloring({'pack': pack, 'adventures': [first, second]}, 2, second)
        # Old bundles retain their existing independent-story production.
        self.assertFalse(is_paired_coloring({'pack': 'Super Héros'}, 2, {'book_style': 'coloring'}))
        with self.assertRaises(ValueError):
            is_paired_coloring({'pack': 'Super Héros', 'adventures': [first, second]}, 2, dict(second, title='Different'))

    def test_worker_uses_the_color_source_without_generating_a_second_story(self):
        import order_production
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'final_books/adventure_01/colored'
            source.mkdir(parents=True)
            (source/'Adam_Same_title.pdf').write_bytes(b'kept color PDF')
            first = dict(title='Same title', theme='Science', idea='', book_style='colored')
            second = dict(first, book_style='coloring', paired_version=PAIR_VERSION,
                          image_only=True, shared_story_from=1)
            order = dict(order_ref='TEST', pack='Super Héros', child_name='Adam', age=7,
                         language='Français', adventures=[first, second], generated_files=[], _dir=root)
            def paired(source_dir, output_dir, pdf, **kwargs):
                self.assertEqual(source_dir, source)
                pdf.write_bytes(b'image only PDF')
                return pdf
            engine = MagicMock()
            with patch.dict('sys.modules', {'book_engine': engine}), \
                 patch('paired_books.build_paired_coloring', side_effect=paired) as convert, \
                 patch.object(order_production, 'get_supabase_client', return_value=MagicMock()), \
                 patch.object(order_production, 'ensure_order_assets', return_value=(Path('ref.png'), [Path('cover.png')]*2)), \
                 patch.object(order_production, 'storage_upload'), \
                 patch.object(order_production, 'update_order_fields'):
                files = order_production.generate_order(order)
            self.assertEqual(len(files), 2)
            convert.assert_called_once()
            engine.generate_book_from_adventure.assert_not_called()
