from pathlib import Path
import ast
import shutil
import tempfile
import unittest
import pdfplumber
from pypdf import PdfReader

from book_layout import DEFAULT_LAYOUT, split_narrative, build_book_pdf
from book_content import story_pages, keepsake_congratulations

ROOT = Path(__file__).resolve().parents[1]


class BookLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sample = ROOT/"output/pdf/itar-maquette-livre-coloriage.pdf"
        if not sample.exists():
            from examples.build_itar_sample import main
            main()

    def test_long_narrative_keeps_all_words_and_readable_font(self):
        text = "Itar découvre un étrange ballon et encourage ses amis. " * 90
        parts = split_narrative(text)
        self.assertGreater(len(parts), 1)
        self.assertEqual(" ".join(parts), " ".join(text.split()))
        with tempfile.TemporaryDirectory() as folder:
            output = build_book_pdf(Path(folder)/"long.pdf", [{"title": "Un étrange ballon", "text": text,
                "image": ROOT/"examples/itar/story-illustration-v2.png"}], ROOT/"examples/itar/medallion.png",
                child_name="Itar", congratulations="Bravo pour ton courage !")
            reader = PdfReader(output)
            self.assertEqual(len(reader.pages), len(parts)+1)
            with pdfplumber.open(output) as pdf:
                for page in pdf.pages[:-1]:
                    self.assertTrue(any(abs(c["size"]-14)<.1 for c in page.chars))
                    self.assertTrue(all(c["x0"] >= 20 and c["x1"] <= page.width-20 and c["top"]>=20 and c["bottom"]<=page.height-15 for c in page.chars))

    def test_sample_has_correct_accents_and_separate_image_and_story(self):
        sample = ROOT/"output/pdf/itar-maquette-livre-coloriage.pdf"
        with pdfplumber.open(sample) as pdf:
            self.assertEqual(len(pdf.pages), 2)
            page = pdf.pages[0]
            self.assertIn("Le panier décisif", page.extract_text())
            body = [c for c in page.chars if abs(c["size"]-14)<.1]
            self.assertLess(page.images[0]["bottom"], min(c["top"] for c in body))
            last = pdf.pages[1]
            text = last.extract_text()
            for expected in ("Bravo, Itar !", "Petit héros, grande imagination", "Colorié par", "Imagine ta prochaine aventure"):
                self.assertIn(expected, text)
            congratulations = [c for c in last.chars if abs(c["size"]-14)<.1 and c["top"]<160]
            self.assertLess(max(c["bottom"] for c in congratulations), last.images[0]["top"])
            self.assertGreaterEqual(DEFAULT_LAYOUT.drawing_height*25.4/72, 85)

    def test_story_metadata_does_not_leak_into_narrative_or_scene(self):
        story = "PAGE 1\nTitre : Découverte\nTexte : Itar écoute ses amis.\nScène à illustrer : Itar avec son équipe.\nSOUVENIR\nFélicitations : Tu as encouragé tes amis !"
        page = story_pages(story, 1)[0]
        self.assertEqual(page["scene"], "Itar avec son équipe.")
        self.assertEqual(keepsake_congratulations(story), "Tu as encouragé tes amis !")

    def test_production_pdf_entrypoint_uses_new_layout_and_keeps_story(self):
        tree = ast.parse((ROOT/"generate_book.py").read_text(encoding="utf-8"))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "generate_pdf")
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            shutil.copyfile(ROOT/"examples/itar/story-illustration-v2.png", folder/"page_01.png")
            story = folder/"story.txt"
            story.write_text("PAGE 1\nTitre : Le panier décisif\nTexte : Itar encourage son équipe et marque un panier.\nScène à illustrer : Itar au basket.", encoding="utf-8")
            namespace = dict(Path=Path, story_pages=story_pages, keepsake_congratulations=keepsake_congratulations,
                build_book_pdf=build_book_pdf, STORY_FILE=story, NUMBER_OF_PAGES=1, PAGES_FOLDER=folder,
                OUTPUT_FILE=folder/"book.pdf", KEEPSAKE_IMAGE=ROOT/"examples/itar/medallion.png", NAME="Itar",
                THEME="Basket", LANGUAGE="Français", CHILD_GENDER="boy", COVER_FILE=folder/"page_01.png")
            exec(compile(ast.Module(body=[function], type_ignores=[]), "generate_book.py", "exec"), namespace)
            output = namespace["generate_pdf"]()
            pdf = PdfReader(output)
            self.assertEqual(len(pdf.pages), 3)
            self.assertIn("Itar encourage son équipe et marque un panier.", pdf.pages[1].extract_text())
            self.assertIn("Bravo, Itar !", pdf.pages[2].extract_text())


if __name__ == "__main__":
    unittest.main()
