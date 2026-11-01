import ast
from pathlib import Path
import re
import unittest

from book_content import normalize_story_structure, story_pages


class StoryStructureTests(unittest.TestCase):
    def test_spanish_saved_story_with_values_on_next_line(self):
        story = ('PAGE 1\nTítulo :  \nSalima, la princesa\nTexto :\n'
                 'Salima dice: «¡Vamos!»\nScène à illustrer :\nUna ciudad.\n'
                 'PERSONNAGES_JSON\n{"appearance":"Texto : unchanged"}')
        fixed = normalize_story_structure(story)
        self.assertEqual(fixed, normalize_story_structure(fixed))
        self.assertIn('"Texto : unchanged"', fixed)
        page = story_pages(story, 1)[0]
        self.assertEqual(page['title'], 'Salima, la princesa')
        self.assertEqual(page['text'], 'Salima dice: «¡Vamos!»')
        tree = ast.parse(Path('generate_book.py').read_text(encoding='utf-8'))
        functions = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)
            and n.name in {'get_page', 'extract_title', 'extract_book_title'}], type_ignores=[])
        namespace = dict(re=re, NAME='Salima', normalize_story_structure=normalize_story_structure)
        exec(compile(functions, 'generate_book.py', 'exec'), namespace)
        self.assertEqual(namespace['extract_book_title'](story), 'Salima, la princesa')

    def test_inline_labels_and_narrative_remain_unchanged(self):
        story = 'PAGE 1\nTitre : Bonjour\nTexte : Le mot Texto reste ici.\nScène à illustrer : Un jardin.'
        self.assertEqual(normalize_story_structure(story), story)
        self.assertEqual(story_pages(story, 1)[0]['text'], 'Le mot Texto reste ici.')
