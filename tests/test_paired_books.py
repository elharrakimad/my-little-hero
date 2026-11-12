import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from paired_books import build_paired_coloring, is_paired_coloring, PAIR_VERSION, validate_clean_lineart, color_to_lineart

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
    def setUp(self):
        # Offline fixture only. Production uses images.edit, never an edge filter.
        from PIL import Image, ImageDraw
        def clean_fixture(source, target, **kwargs):
            with Image.open(source) as original:
                image = Image.new('L', original.size, 255)
            draw = ImageDraw.Draw(image)
            draw.ellipse((100,100,500,700),outline=0,width=7)
            image.save(target)
            image.close()
        self.redraw = patch('paired_books.color_to_lineart', side_effect=clean_fixture)
        self.redraw.start()
        self.addCleanup(self.redraw.stop)

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
            # Resume reuses checked outputs, without paying for the pages again.
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

    def test_quality_gate_rejects_texture_noise_and_gray_shading(self):
        from PIL import Image, ImageDraw
        import random
        for kind in ('noise', 'gray'):
            with self.subTest(kind=kind):
                image=Image.new('L',(300,400),255)
                if kind == 'noise':
                    pixels=image.load()
                    rng=random.Random(41)
                    for _ in range(24000): pixels[rng.randrange(300),rng.randrange(400)]=0
                else:
                    ImageDraw.Draw(image).rectangle((0,0,299,200),fill=130)
                with self.assertRaises(ValueError): validate_clean_lineart(image)
                image.close()

    def test_actual_redraw_uses_source_reference_and_clean_line_prompt(self):
        import base64,io
        from types import SimpleNamespace
        from PIL import Image,ImageDraw
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory)
            source=directory/'source.png'
            Image.new('RGB',(400,600),'red').save(source)
            image=Image.new('L',(400,600),255)
            ImageDraw.Draw(image).ellipse((50,50,350,550),outline=0,width=5)
            encoded=io.BytesIO();image.save(encoded,format='PNG');image.close()
            client=MagicMock()
            client.images.edit.return_value=SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(encoded.getvalue()).decode())])
            target=directory/'clean.png'
            color_to_lineart(source,target,scene='Une princesse règle un moulin.',client=client)
            self.assertTrue(target.exists())
            args=client.images.edit.call_args.kwargs
            self.assertIn('PAS un filtre',args['prompt'])
            self.assertIn('Aucun texte',args['prompt'])
            self.assertIn('Une princesse règle un moulin.',args['prompt'])
            self.assertEqual(args['image'][0].name,str(source))
            self.assertTrue(args['image'][0].closed)

    def test_interruption_reuses_verified_pages_and_never_old_filter_output(self):
        from PIL import Image,ImageDraw
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=source_book(root/'source');out=root/'out'
            calls=[]
            def redraw(src,target,**kwargs):
                calls.append(src.name)
                if len(calls)==3: raise RuntimeError('interrupted')
                image=Image.new('L',(400,600),255)
                ImageDraw.Draw(image).ellipse((50,50,350,550),outline=0,width=5)
                image.save(target);image.close()
            with patch('paired_books.color_to_lineart',side_effect=redraw):
                with self.assertRaises(RuntimeError):build_paired_coloring(source,out,out/'book.pdf')
            self.assertTrue((out/'pages/page_01.verified.json').exists())
            self.assertFalse((out/'book.pdf').exists())
            with patch('paired_books.color_to_lineart',side_effect=redraw) as resumed:
                build_paired_coloring(source,out,out/'book.pdf')
                self.assertEqual(resumed.call_count,8)
            # Old filtered images have no v2 checkpoint and must be redrawn.
            (out/'pages/page_01.verified.json').unlink()
            with patch('paired_books.color_to_lineart',side_effect=redraw) as repair:
                build_paired_coloring(source,out,out/'book.pdf')
                self.assertEqual(repair.call_count,1)
