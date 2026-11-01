from pathlib import Path
import tempfile
import unittest
import pdfplumber
from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics

from arabic_layout import has_arabic, visual_line
from book_layout import paragraph, split_narrative, build_book_pdf, souvenir_copy
from book_content import keepsake_congratulations

ROOT = Path(__file__).resolve().parents[1]


class ArabicLayoutTests(unittest.TestCase):
    def test_shaping_coverage_and_mixed_numbers_are_preserved(self):
        sample = "أَحْسَنْتَ يا إيتار! Itar 16 — المغامرة 2026."
        item = paragraph(sample)
        item.wrap(480, 1000)
        visual = visual_line(sample)
        self.assertIn("2026", visual)
        self.assertIn("Itar 16", visual)
        self.assertNotEqual(visual, sample)
        coverage = pdfmetrics.getFont(item.font).face.charToGlyph
        for ch in visual:
            if not ch.isspace():
                self.assertIn(ord(ch), coverage, repr(ch))

    def test_wrap_keeps_logical_reading_order_then_shapes_each_line(self):
        text = "اكتشف إيتار برجا عاليا وساعد أصدقاءه على عبور الجسر بأمان. " * 20
        parts = split_narrative(text)
        self.assertEqual(" ".join(parts), " ".join(text.split()))
        self.assertGreater(len(parts), 1)
        for part in parts:
            item = paragraph(part)
            _, height = item.wrap(468, 130)
            self.assertLessEqual(height, 130)
            self.assertEqual(" ".join(item.logical_lines), part)
            for line in item.logical_lines:
                self.assertLessEqual(pdfmetrics.stringWidth(visual_line(line), item.font, item.size), 468)

    def test_pdf_embeds_arabic_fonts_and_keeps_text_inside_printable_area(self):
        from examples.build_arabic_sample import main
        output = main()
        reader = PdfReader(output)
        self.assertEqual(len(reader.pages), 2)
        fonts = [str(font.get_object().get("/BaseFont", "")) for page in reader.pages
            for font in page["/Resources"]["/Font"].get_object().values()]
        self.assertTrue(any("Amiri-Regular" in f for f in fonts))
        self.assertTrue(any("Amiri-Bold" in f for f in fonts))
        with pdfplumber.open(output) as pdf:
            for page in pdf.pages:
                self.assertTrue(all(c["x0"] >= 20 and c["x1"] <= page.width-20
                    and c["top"]>=20 and c["bottom"]<=page.height-15 for c in page.chars))
                self.assertNotIn("\u25a0", page.extract_text())

    def test_arabic_souvenir_and_continuation_have_no_french_labels(self):
        self.assertTrue(all(has_arabic(s) for s in souvenir_copy("إيتار", language="العربية")))
        self.assertIn("بطلة", souvenir_copy("سارة", gender="girl", language="العربية")[1])
        self.assertTrue(has_arabic(keepsake_congratulations("", language="العربية")))
        with tempfile.TemporaryDirectory() as folder:
            output = build_book_pdf(Path(folder)/"continued.pdf", [{"title":"المغامرة", "text":"ساعد إيتار أصدقاءه. "*100,
                "image":ROOT/"examples/itar/story-illustration-v2.png"}], ROOT/"examples/itar/medallion.png",
                child_name="إيتار", congratulations="أحسنت!", language="العربية")
            reader = PdfReader(output)
            self.assertGreater(len(reader.pages),2)
            self.assertNotIn("suite", " ".join(p.extract_text() for p in reader.pages))
