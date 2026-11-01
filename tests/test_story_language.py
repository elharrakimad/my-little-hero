import json
import ast
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from book_content import story_pages
from story_language import arabic_text_is_valid, validate_printed_language, repair_arabic_story, story_language_instruction


def mixed_story():
    return ('PAGE 1\nTitre : إيتار والمغامرة\nTexte : بدأ إيتار رحلته مع أصدقائه.\n'
        'Scène à illustrer : Itar dans un village.\n'
        'PAGE 2\nTitre : الرival ذو carapace verte\nTexte : شاهد إيتار rival قرب الجبل.\n'
        'Scène à illustrer : Itar et son rival à la carapace verte.\n'
        'SOUVENIR\nFélicitations : لقد أنجزت مهمتك!\nPERSONNAGES_JSON\n'
        '{"characters":[{"id":"rival","name":"Rival","appearance":"Carapace verte","pages":[2]}]}')


class StoryLanguageTests(unittest.TestCase):
    def client(self, result):
        client = MagicMock()
        client.responses.create.return_value = SimpleNamespace(output_text=result)
        return client

    def test_detects_the_mixed_title_from_screenshot_and_latin_names(self):
        for text in ('الرival ذو carapace verte', 'خصم rival', 'Itar', 'été', '123'):
            self.assertFalse(arabic_text_is_valid(text), text)
        for text in ('المنافس ذو الدرع الأخضر', 'أَحْسَنْتَ يا إيتار!', 'المغامرة 16'):
            self.assertTrue(arabic_text_is_valid(text), text)
        with self.assertRaisesRegex(ValueError, 'page_2_title'):
            validate_printed_language(mixed_story(), 'العربية', 2)

    def test_one_text_correction_preserves_scenes_cast_and_approved_title(self):
        original = mixed_story()
        replacements = {'page_2_title': 'المنافس ذو الدرع الأخضر', 'page_2_text': 'شاهد إيتار منافسا قرب الجبل.'}
        client = self.client(json.dumps(replacements, ensure_ascii=False))
        result = repair_arabic_story(original, 'العربية', client, 'إيتار والمغامرة', 2)
        validate_printed_language(result, 'العربية', 2)
        self.assertEqual(client.responses.create.call_count, 1)
        client.images.edit.assert_not_called()
        before, after = story_pages(original, 2), story_pages(result, 2)
        self.assertEqual(before[0], after[0])
        self.assertEqual([p['scene'] for p in before], [p['scene'] for p in after])
        self.assertEqual(original.split('PERSONNAGES_JSON')[1], result.split('PERSONNAGES_JSON')[1])
        self.assertEqual(after[1]['title'], replacements['page_2_title'])
        self.assertEqual(repair_arabic_story(result, 'العربية', client, 'إيتار والمغامرة', 2), result)
        self.assertEqual(client.responses.create.call_count, 1)

    def test_invalid_translation_stops_without_loop_or_partial_changes(self):
        for result in ('not json', json.dumps({'page_2_title':'عنوان'}),
                json.dumps({'page_2_title':'عنوان rival', 'page_2_text':'نص عربي'}),
                json.dumps({'page_2_title':'عنوان', 'page_2_text':'نص عربي', 'scene':'MODIFIED'})):
            client = self.client(result)
            original = mixed_story()
            with self.assertRaises(ValueError):
                repair_arabic_story(original, 'العربية', client, 'إيتار والمغامرة', 2)
            self.assertEqual(client.responses.create.call_count, 1)
            self.assertIn('carapace verte', original)

    def test_cover_title_is_never_silently_translated(self):
        client = MagicMock()
        with self.assertRaises(ValueError):
            repair_arabic_story(mixed_story().replace('إيتار والمغامرة','Itar والمغامرة'), 'العربية', client, 'Itar والمغامرة', 2)
        client.responses.create.assert_not_called()

    def test_pdf_entrypoint_refuses_unrepaired_mixed_text(self):
        tree = ast.parse(Path('generate_book.py').read_text(encoding='utf-8'))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'generate_pdf')
        with tempfile.TemporaryDirectory() as folder:
            story = Path(folder)/'story.txt'
            story.write_text(mixed_story(), encoding='utf-8')
            builder = MagicMock()
            ns = dict(Path=Path, STORY_FILE=story, LANGUAGE='العربية', NUMBER_OF_PAGES=2,
                validate_printed_language=validate_printed_language, build_book_pdf=builder)
            exec(compile(ast.Module(body=[function], type_ignores=[]), 'generate_book.py', 'exec'), ns)
            with self.assertRaisesRegex(ValueError, 'page_2_title'):
                ns['generate_pdf']()
            builder.assert_not_called()

    def test_other_languages_are_unchanged_and_arabic_instructions_keep_technical_labels(self):
        client = MagicMock()
        for language in ('Français', 'English', 'Español'):
            self.assertEqual(repair_arabic_story('Any existing content', language, client, 'Title'), 'Any existing content')
        client.responses.create.assert_not_called()
        instruction = story_language_instruction('العربية')
        self.assertIn('carapace verte', instruction)
        self.assertIn('PERSONNAGES_JSON', instruction)
        self.assertIn('exclusivement arabe', instruction)
