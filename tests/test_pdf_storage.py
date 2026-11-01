from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from PIL import Image
from pypdf import PdfReader

from book_layout import build_book_pdf
from pdf_storage import is_payload_too_large, optimize_saved_pdf
import order_production

ROOT = Path(__file__).resolve().parents[1]


class PdfStorageTests(unittest.TestCase):
    def test_color_pdf_uses_jpeg_at_original_resolution_and_keeps_real_text(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            image = folder/'color.png'
            Image.frombytes('RGB',(900,1300),random.Random(42).randbytes(900*1300*3)).save(image)
            pages = [{'title':'Lecture en couleur','text':'Itar retrouve ses amis.','image':image}]
            args = dict(child_name='Itar',congratulations='Bravo pour cette aventure !')
            raw = build_book_pdf(folder/'raw.pdf',pages,image,**args)
            compact = build_book_pdf(folder/'compact.pdf',pages,image,book_style='colored',**args)
            self.assertLess(compact.stat().st_size,raw.stat().st_size*.85)
            reader = PdfReader(compact)
            self.assertEqual(len(reader.pages),2)
            self.assertIn('Itar retrouve ses amis.',reader.pages[0].extract_text())
            self.assertIn('Lu par',reader.pages[1].extract_text())
            images = list(reader.pages[0].images)
            self.assertTrue(images)
            self.assertEqual(images[0].image.size,(900,1300))
            self.assertEqual(images[0].image.mode,'RGB')
            self.assertTrue(any('DCTDecode' in str(obj.get_object().get('/Filter'))
                for obj in reader.pages[0]['/Resources']['/XObject'].get_object().values()))

    def test_missing_saved_assets_never_trigger_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf=Path(directory)/'book.pdf';pdf.write_bytes(b'original PDF')
            with self.assertRaises(FileNotFoundError):
                optimize_saved_pdf(pdf,{'language':'Français'}, {'theme':'Science'})
            self.assertEqual(pdf.read_bytes(),b'original PDF')

    def test_413_upload_is_rebuilt_offline_then_uploaded_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            folder=root/'final_books/adventure_01/colored';folder.mkdir(parents=True)
            pdf=folder/'Itar_Aventure.pdf';pdf.write_bytes(b'existing PDF')
            order={'order_ref':'TEST','child_name':'Itar','age':12,'language':'Français','_dir':root,
                'adventures':[{'title':'Aventure','theme':'Science','book_style':'colored'}],
                'generated_files':[], 'generation_progress':{'upload_only':True}}
            engine=MagicMock()
            with patch.dict('sys.modules',{'book_engine':engine}), \
                patch.object(order_production,'get_supabase_client',return_value=MagicMock()), \
                patch.object(order_production,'ensure_order_assets',return_value=(Path('ref.png'),[Path('cover.png')])), \
                patch.object(order_production,'update_order_fields'), \
                patch.object(order_production,'storage_upload',return_value=None) as upload, \
                patch.object(order_production,'optimize_saved_pdf',return_value=pdf) as optimize:
                result=order_production.generate_order(order)
                self.assertEqual(upload.call_count,1)
                optimize.assert_called_once_with(pdf,order,order['adventures'][0])
                # Updating a ready book's layout must not skip its existing remote PDF.
                order['generation_progress']={'upload_only':True,'rebuild_layout':True}
                order_production.generate_order(order)
                self.assertEqual(upload.call_count,2)
                self.assertTrue(optimize.call_args.kwargs['force_layout'])
            engine.generate_book_from_adventure.assert_not_called()
            self.assertEqual(order['status'],'BOOKS_READY')
            self.assertEqual(result,['orders/TEST/final_books/adventure_01/book_01.pdf'])

    def test_upload_only_resume_cannot_generate_if_pdf_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            order={'order_ref':'TEST','child_name':'Itar','age':12,'language':'Français','_dir':Path(directory),
                'adventures':[{'title':'Aventure','theme':'Science','book_style':'colored'}],
                'generated_files':[], 'generation_progress':{'upload_only':True}}
            engine=MagicMock()
            with patch.dict('sys.modules',{'book_engine':engine}), \
                patch.object(order_production,'get_supabase_client',return_value=MagicMock()), \
                patch.object(order_production,'ensure_order_assets',return_value=(Path('ref.png'),[Path('cover.png')])), \
                patch.object(order_production,'update_order_fields'):
                with self.assertRaisesRegex(FileNotFoundError,'aucun appel IA'):
                    order_production.generate_order(order)
            engine.generate_book_from_adventure.assert_not_called()

    def test_only_size_failures_enable_optimization(self):
        self.assertTrue(is_payload_too_large("{'statusCode': 413, 'error': Payload too large}"))
        self.assertFalse(is_payload_too_large('400 moderation_blocked'))
        self.assertFalse(is_payload_too_large('500 timeout'))
