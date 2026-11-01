from pathlib import Path
import tempfile
import unittest
import pdfplumber
from pypdf import PdfReader
from book_layout import build_book_pdf, DEFAULT_LAYOUT
from book_style import page_composition

ROOT=Path(__file__).resolve().parents[1]


class FullColorLayoutTests(unittest.TestCase):
    def test_color_image_covers_a4_and_all_story_text_is_in_top_panel(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf=build_book_pdf(Path(directory)/'full.pdf',[{'title':'The Choice at the Cascade',
                'text':'Itar follows the quiet path and helps his friends reach the valley safely.',
                'image':ROOT/'web/assets/cover_02.png'}],ROOT/'examples/itar/medallion.png',
                child_name='Itar',congratulations='You found the right path!',book_style='colored',language='English')
            with pdfplumber.open(pdf) as document:
                page=document.pages[0]; image=page.images[0]
                self.assertLessEqual(image['x0'],0.01)
                self.assertGreaterEqual(image['x1'],page.width-.01)
                self.assertLessEqual(image['top'],.01)
                self.assertGreaterEqual(image['bottom'],page.height-.01)
                title=[c for c in page.chars if abs(c['size']-23)<.1]
                body=[c for c in page.chars if abs(c['size']-14)<.1]
                self.assertLess(max(c['bottom'] for c in title),min(c['top'] for c in body))
                self.assertLess(max(c['bottom'] for c in body),page.height*.35)
                self.assertTrue(all(c['x0']>DEFAULT_LAYOUT.binding_margin and c['x1']<page.width-DEFAULT_LAYOUT.outer_margin for c in body))

    def test_long_arabic_story_continues_without_shrinking_or_losing_content(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf=build_book_pdf(Path(directory)/'arabic.pdf',[{'title':'إيتار والمغامرة',
                'text':'ساعد إيتار أصدقاءه على عبور الجسر بأمان. '*35,
                'image':ROOT/'web/assets/cover_02.png'}],ROOT/'examples/itar/medallion.png',
                child_name='إيتار',congratulations='أحسنت!',book_style='colored',language='العربية')
            self.assertGreater(len(PdfReader(pdf).pages),2)
            with pdfplumber.open(pdf) as document:
                for page in document.pages[:-1]:
                    body=[c for c in page.chars if abs(c['size']-14)<.1]
                    self.assertTrue(body)
                    self.assertLess(max(c['bottom'] for c in body),page.height*.35)

    def test_only_color_pages_request_edge_to_edge_composition(self):
        self.assertIn('aucune marge blanche',page_composition('colored'))
        self.assertIn('tiers supérieur',page_composition('colored'))
        self.assertIn('vignette',page_composition('coloring'))
