import ast
import json
from pathlib import Path
import unittest

from game_story import game_story_instruction


class GameStoryTests(unittest.TestCase):
    def test_all_games_have_console_opening_without_affecting_other_categories(self):
        source = Path('theme-catalog.js').read_text(encoding='utf-8')
        rows, _ = json.JSONDecoder().raw_decode(source.split('window.MLH_THEME_CATALOG =', 1)[1].lstrip())
        games = 0
        for row in rows:
            for value in (row['theme'], row['label'], row['ar']):
                instruction = game_story_instruction(value)
                if row['category'] == 'video-games':
                    self.assertIn('PAGE 1 commence dans le monde réel', instruction)
                    self.assertIn('console de jeu', instruction)
                    self.assertIn('transporte', instruction)
                    self.assertIn('PAGE 2', instruction)
                    self.assertIn('dix scènes existantes', instruction)
                else:
                    self.assertEqual(instruction, '')
            games += row['category'] == 'video-games'
        self.assertEqual(games, 51)
        self.assertEqual(game_story_instruction('Mon propre thème'), '')

    def test_production_story_prompt_includes_the_opening_rule(self):
        tree = ast.parse(Path('generate_book.py').read_text(encoding='utf-8'))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'generate_story')
        self.assertTrue(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == 'game_story_instruction' for n in ast.walk(function)))
