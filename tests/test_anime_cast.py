import ast
import base64
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

import anime_cast
import character_continuity as continuity
from age_profile import coloring_instruction


def cast_story(count=2):
    return 'PERSONNAGES_JSON\n' + json.dumps({"characters": [
        {"id": f"ami_{i}", "name": f"Ami {i}", "appearance": f"Coiffure fixe {i}, veste et accessoire distinctifs {i}.", "pages": [1, 2, 10]}
        for i in range(count)]})


class AnimeCastTests(unittest.TestCase):
    def test_all_anime_catalogue_values_get_two_secondary_limit_only(self):
        self.assertTrue(anime_cast.anime_themes())
        for theme in anime_cast.anime_themes():
            self.assertEqual(anime_cast.cast_limit(theme), 2)
            self.assertIn('Deux personnages secondaires au maximum', anime_cast.anime_cast_instruction(theme))
        self.assertEqual(anime_cast.cast_limit('Science'), 6)
        self.assertEqual(anime_cast.anime_cast_instruction('Science'), '')
        with self.assertRaisesRegex(ValueError, 'maximum 2'):
            continuity.cast_from_story(cast_story(3), max_characters=2)
        self.assertEqual(len(continuity.cast_from_story(cast_story(3))), 3)
        for count in (0, 1, 2):
            self.assertEqual(len(continuity.cast_from_story(cast_story(count), max_characters=2)), count)

    def namespace(self, folder, story):
        tree = ast.parse(Path('generate_book.py').read_text(encoding='utf-8'))
        functions = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)
            and n.name in {'generate_secondary_character_references', 'atomic_write_bytes'}], type_ignores=[])
        for name in ['child.png', 'cover.png']:
            (folder/name).write_bytes(b'image')
        (folder/'story.txt').write_text(story, encoding='utf-8')
        client = MagicMock()
        client.images.edit.return_value = SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(b'fixed secondary reference').decode())])
        ns = dict(Path=Path, base64=base64, ExitStack=contextlib.ExitStack,
            secondary_reference_folder=anime_cast.secondary_reference_folder,
            secondary_reference_path=anime_cast.secondary_reference_path,
            cast_from_story=continuity.cast_from_story, reference_roles=continuity.reference_roles,
            coloring_instruction=coloring_instruction, THEME=next(iter(anime_cast.anime_themes())),
            AGE=12, NUMBER_OF_PAGES=10, PAGES_FOLDER=folder/'pages', STORY_FILE=folder/'story.txt',
            REFERENCE_IMAGE=folder/'child.png', COVER_FILE=folder/'cover.png', client=client)
        exec(compile(functions, 'generate_book.py', 'exec'), ns)
        return ns, client

    def test_two_dedicated_references_are_cached_and_sent_on_each_appearance(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            folder = Path(directory)
            ns, client = self.namespace(folder, cast_story())
            progress = MagicMock()
            ns['generate_secondary_character_references'](progress)
            self.assertEqual(client.images.edit.call_count, 2)
            self.assertEqual(progress.call_count, 2)
            refs_folder = folder/'secondary_references'
            self.assertEqual(len(list(refs_folder.glob('*.png'))), 2)
            handles = [h for call in client.images.edit.call_args_list for h in call.kwargs['image']]
            self.assertTrue(all(h.closed for h in handles))
            ns['generate_secondary_character_references'](progress)
            self.assertEqual(client.images.edit.call_count, 2)
            for page in (1, 2, 10):
                refs = continuity.reference_paths(cast_story(), page, folder/'child.png', folder/'cover.png', folder/'pages', secondary_folder=refs_folder)
                self.assertEqual(sum(path.parent == refs_folder for path, _ in refs), 2)
            # A partial restart reuses the finished reference, without changing its bytes.
            saved = sorted(refs_folder.glob('*.png'))
            saved[1].unlink()
            ns['generate_secondary_character_references']()
            self.assertEqual(client.images.edit.call_count, 3)
            self.assertEqual(saved[0].read_bytes(), b'fixed secondary reference')

    def test_third_secondary_stops_before_any_paid_reference_request(self):
        with tempfile.TemporaryDirectory() as directory:
            ns, client = self.namespace(Path(directory), cast_story(3))
            with self.assertRaisesRegex(ValueError, 'maximum 2'):
                ns['generate_secondary_character_references']()
            client.images.edit.assert_not_called()

    def test_non_anime_legacy_and_solo_stories_add_no_paid_reference_call(self):
        for theme, story in [('Science', cast_story()), (next(iter(anime_cast.anime_themes())), 'Ancien récit'),
                (next(iter(anime_cast.anime_themes())), cast_story(0))]:
            with tempfile.TemporaryDirectory() as directory:
                ns, client = self.namespace(Path(directory), story)
                ns['THEME'] = theme
                ns['generate_secondary_character_references']()
                client.images.edit.assert_not_called()

    def test_profiles_are_separate_per_book_and_appearance_change_invalidates_cache(self):
        character = continuity.cast_from_story(cast_story())[0]
        first = anime_cast.secondary_reference_path('book_one/secondary_references', character)
        self.assertNotEqual(first, anime_cast.secondary_reference_path('book_two/secondary_references', character))
        self.assertNotEqual(first, anime_cast.secondary_reference_path('book_one/secondary_references', {**character, 'appearance':'Nouvelle tenue'}))
