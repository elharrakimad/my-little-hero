import ast
import contextlib
import io
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from child_profile import gender_instruction


class BookEngineTests(unittest.TestCase):
    def test_gender_reaches_engine_and_resets_for_legacy_order(self):
        engine = MagicMock()
        engine.get_book_title.side_effect = lambda: engine.BOOK_TITLE
        engine.generate_pdf.side_effect = lambda: Path(engine.OUTPUT_FILE).write_bytes(b"test pdf")
        with patch.dict("sys.modules", {"generate_book": engine}):
            wrapper = runpy.run_path("book_engine.py")["generate_book_from_adventure"]
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            for gender in ("girl", "boy", ""):
                result = wrapper(child_name="Camille", age=7, theme="Science",
                    language="Français", child_gender=gender, client_idea="Une découverte",
                    child_quality="Curiosité", book_title="La découverte",
                    reference_path="reference.png", output_dir=Path(directory) / (gender or "legacy"))
                self.assertEqual(engine.CHILD_GENDER, gender)
                self.assertEqual(engine.CLIENT_IDEA, "Une découverte")
                self.assertTrue(result.exists())

    def test_story_prompt_uses_gender_for_every_language(self):
        tree = ast.parse(Path("generate_book.py").read_text(encoding="utf-8"))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "generate_story")
        for gender, expected in (("girl", "une fille"), ("boy", "un garçon")):
            for language in ("Français", "العربية", "English", "Español"):
                client = MagicMock()
                client.responses.create.return_value.output_text = "PAGE 1\nTitre"
                with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
                    namespace = dict(Path=Path, gender_instruction=gender_instruction, client=client,
                        CHILD_GENDER=gender, NAME="Camille", AGE=7, THEME="Science", LANGUAGE=language,
                        CLIENT_IDEA="", CHILD_QUALITY="", BOOK_TITLE="Titre", NUMBER_OF_PAGES=10,
                        STORY_FILE=str(Path(directory) / "story.txt"))
                    exec(compile(ast.Module(body=[function], type_ignores=[]), "generate_book.py", "exec"), namespace)
                    namespace["generate_story"]()
                    prompt = client.responses.create.call_args.kwargs["input"]
                    self.assertIn(expected, prompt)
                    self.assertIn(language, prompt)
                    self.assertIn("conjugaison", prompt)

    def test_all_generation_prompts_receive_profile(self):
        tree = ast.parse(Path("generate_book.py").read_text(encoding="utf-8"))
        for name in ("generate_story", "generate_character_reference", "generate_page", "generate_cover"):
            function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
            self.assertTrue(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "gender_instruction" for n in ast.walk(function)), name)


if __name__ == "__main__":
    unittest.main()
