import ast
from pathlib import Path
import re
import unittest

from age_profile import coloring_instruction


class AgeProfileTests(unittest.TestCase):
    def test_every_offered_age_has_the_expected_difficulty(self):
        for age in range(3, 17):
            expected = "très facile" if age <= 5 else "difficulté facile" if age <= 8 else "intermédiaire" if age <= 12 else "avancée"
            instruction = coloring_instruction(age)
            self.assertIn(expected, instruction)
            self.assertIn(f"{age} ans", instruction)
            self.assertIn("taille A4", instruction)
        self.assertIn("moins enfantin", coloring_instruction(16))
        self.assertNotEqual(coloring_instruction(4), coloring_instruction(16))

    def test_form_offers_all_ages_from_three_to_sixteen(self):
        html = Path("index.html").read_text(encoding="utf-8")
        options = re.search(r'id="childAge"(.*?)</select>', html, re.S).group(1)
        self.assertEqual([int(v) for v in re.findall(r'<option>(\d+) ans</option>', options)], list(range(3, 17)))

    def test_story_pages_and_medallion_share_age_art_direction(self):
        tree = ast.parse(Path("generate_book.py").read_text(encoding="utf-8"))
        for name in ("generate_story", "generate_page", "generate_keepsake_medallion"):
            function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
            self.assertTrue(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "coloring_instruction" for n in ast.walk(function)), name)
