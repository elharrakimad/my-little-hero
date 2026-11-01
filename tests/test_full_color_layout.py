from pathlib import Path
import tempfile
import unittest
import pdfplumber
from pypdf import PdfReader
from book_layout import build_book_pdf, DEFAULT_LAYOUT
from book_style import page_composition

ROOT=Path(__file__).resolve().parents[1]


class FullColorLayoutTests(unittest.TestCase):
    def test_color_image_has_no_text_and_story_is_on_its_own_page(self):
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
                self.assertFalse(page.extract_text())
                self.assertEqual(len(document.pages),3)
                story=document.pages[1]
                title=[c for c in story.chars if abs(c['size']-27)<.1]
                body=[c for c in story.chars if abs(c['size']-17)<.1]
                self.assertLess(max(c['bottom'] for c in title),min(c['top'] for c in body))
                self.assertTrue(all(c['x0']>=69 and c['x1']<=page.width-69 for c in body))
                self.assertEqual(str(PdfReader(pdf).trailer['/Root']['/PageLayout']),'/TwoPageLeft')

    def test_long_arabic_story_continues_without_shrinking_or_losing_content(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf=build_book_pdf(Path(directory)/'arabic.pdf',[{'title':'إيتار والمغامرة',
                'text':'ساعد إيتار أصدقاءه على عبور الجسر بأمان. '*35,
                'image':ROOT/'web/assets/cover_02.png'}],ROOT/'examples/itar/medallion.png',
                child_name='إيتار',congratulations='أحسنت!',book_style='colored',language='العربية')
            self.assertGreater(len(PdfReader(pdf).pages),2)
            with pdfplumber.open(pdf) as document:
                for page in document.pages[1:-1:2]:
                    body=[c for c in page.chars if abs(c['size']-17)<.1]
                    self.assertTrue(body)
                    self.assertLess(max(c['bottom'] for c in body),page.height-70)

    def test_only_color_pages_request_edge_to_edge_composition(self):
        self.assertIn('aucune marge blanche',page_composition('colored'))
        self.assertIn('sans aucun titre',page_composition('colored'))
        self.assertIn('vignette',page_composition('coloring'))

    def test_ten_scenes_produce_twenty_color_pages_but_ten_coloring_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            pages=[{'title':f'Aventure {i}','text':'Itar aide ses amis.','image':ROOT/'examples/itar/story-illustration-v2.png'} for i in range(10)]
            for style, count in [('colored',22),('coloring',12)]:
                pdf=build_book_pdf(Path(directory)/f'{style}.pdf',pages,ROOT/'examples/itar/medallion.png',
                    child_name='Itar',congratulations='Bravo !',cover=ROOT/'web/assets/cover_02.png',book_style=style)
                reader=PdfReader(pdf)
                self.assertEqual(len(reader.pages),count) # Includes cover and keepsake.
                if style=='colored':
                    for i in range(1,21,2):
                        self.assertFalse(reader.pages[i].extract_text().strip())
                        self.assertIn('Itar aide',reader.pages[i+1].extract_text())
