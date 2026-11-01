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

import character_continuity as continuity
from child_profile import gender_instruction
from age_profile import coloring_instruction
from story_reference import visual_reference_instruction


def sample_story():
    return ('PAGE 1\nTitre : Départ\nTexte : Itar part.\nScène à illustrer : Itar seul.\n'
        'PAGE 2\nTitre : Rencontre\nTexte : Une amie arrive.\nScène à illustrer : Itar et Lina.\n'
        'SOUVENIR\nFélicitations : Bravo !\nPERSONNAGES_JSON\n' + json.dumps({"characters": [
            {"id": "lina", "name": "Lina", "appearance": "Tresse unique, lunettes rondes, veste courte à deux poches et bottines.", "pages": [2, 5, 8, 10]},
            {"id": "fox", "name": "Renard", "appearance": "Petit renard aux oreilles triangulaires et queue à trois anneaux.", "pages": [3, 6]}]}, ensure_ascii=False))


class ContinuityTests(unittest.TestCase):
    def test_recurring_friend_uses_first_appearance_after_a_long_absence(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            for name in ['child.png', 'cover.png'] + [f'page_{n:02d}.png' for n in range(1, 8)]:
                (folder/name).write_bytes(b'image')
            refs = continuity.reference_paths(sample_story(), 8, folder/'child.png', folder/'cover.png', folder)
            self.assertEqual([p.name for p, _ in refs], ['child.png', 'cover.png', 'page_02.png'])
            context = continuity.continuity_context(sample_story(), 8)
            self.assertIn('Tresse unique', context)
            self.assertIn('Secondaires présents dans cette scène : lina\n', context)
            self.assertNotIn('page_07.png', str(refs))

    def test_no_companions_are_forced_into_a_solo_scene(self):
        context = continuity.continuity_context(sample_story(), 1)
        self.assertIn('Secondaires présents dans cette scène : aucun', context)

    def test_legacy_stories_reuse_existing_images_without_rewriting_story(self):
        legacy = sample_story().split('PERSONNAGES_JSON')[0]
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            for name in ['child.png', 'page_01.png', 'page_02.png']:
                (folder/name).write_bytes(b'image')
            refs = continuity.reference_paths(legacy, 3, folder/'child.png', None, folder)
            self.assertEqual([p.name for p, _ in refs], ['child.png', 'page_01.png', 'page_02.png'])
            self.assertIn('Itar et Lina.', continuity.continuity_context(legacy, 3))

    def test_invalid_roster_stops_before_images_and_metadata_never_enters_printed_scene(self):
        from book_content import story_pages
        self.assertNotIn('PERSONNAGES_JSON', story_pages(sample_story(), 2)[1]['scene'])
        for rows in ([{"id":"x"}], [{"id":"x", "name":"Lina", "appearance":"Tresse", "pages":[11]}]):
            with self.assertRaises(ValueError):
                continuity.cast_from_story('PERSONNAGES_JSON\n'+json.dumps({"characters": rows}))
        self.assertIsNone(continuity.cast_from_story('Ancien récit'))
        self.assertEqual(continuity.cast_from_story('PERSONNAGES_JSON\n{"characters":[]}'), [])

    def test_page_request_actually_sends_anchors_and_closes_files_even_on_error(self):
        tree = ast.parse(Path('generate_book.py').read_text(encoding='utf-8'))
        names = {'generate_page', 'extract_scene', 'extract_title', 'require_file', 'atomic_write_bytes'}
        functions = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[])
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            folder = Path(folder)
            for name in ['child.png', 'cover.png', 'page_02.png']:
                (folder/name).write_bytes(b'image')
            (folder/'story.txt').write_text(sample_story(),encoding='utf-8')
            client = MagicMock()
            handles = []
            def edit(**kw):
                handles.extend(kw['image'])
                self.assertEqual([Path(h.name).name for h in kw['image']], ['child.png','cover.png','page_02.png'])
                self.assertIn('Tresse unique', kw['prompt'])
                self.assertIn('Image 3:', kw['prompt'])
                return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(b'new image').decode())])
            client.images.edit.side_effect = edit
            ns = dict(Path=Path, re=__import__('re'), base64=base64, ExitStack=contextlib.ExitStack,
                gender_instruction=gender_instruction, coloring_instruction=coloring_instruction,
                visual_reference_instruction=visual_reference_instruction,
                continuity_context=continuity.continuity_context, reference_paths=continuity.reference_paths,
                reference_roles=continuity.reference_roles, client=client, CHILD_GENDER='boy', AGE=10, THEME='Forêt',
                PAGES_FOLDER=folder, STORY_FILE=folder/'story.txt', COVER_FILE=folder/'cover.png',
                REFERENCE_IMAGE=folder/'child.png', REUSE_EXISTING_FILES=True, NUMBER_OF_PAGES=10)
            exec(compile(functions, 'generate_book.py', 'exec'), ns)
            ns['generate_page'](8, 'Titre : Retour\nScène à illustrer : Itar retrouve Lina.')
            self.assertEqual(client.images.edit.call_count, 1)
            self.assertTrue(all(h.closed for h in handles))
            self.assertEqual((folder/'page_08.png').read_bytes(), b'new image')
            ns['generate_page'](8, 'cached')
            self.assertEqual(client.images.edit.call_count, 1)
            def reject(**kw):
                handles.extend(kw['image'])
                raise RuntimeError('Simulated rejection')
            client.images.edit.side_effect = reject
            with self.assertRaises(RuntimeError):
                ns['generate_page'](10, 'Titre : Fin\nScène à illustrer : Itar et Lina.')
            self.assertFalse((folder/'page_10.png').exists())
            self.assertTrue(all(h.closed for h in handles))
