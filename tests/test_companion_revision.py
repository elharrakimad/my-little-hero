import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from book_content import story_pages
from companion_revision import LUMO_APPEARANCE, prepare_revision, revised_story


def existing_story():
    return '\n'.join(f'PAGE {i}\nTitre : Adventure {i}\nTexte : Sparky lights the path.\n'
        'Scène à illustrer : Sparky, a small yellow creature with long pointed ears tipped in black, red cheeks, and a lightning-shaped tail, walks beside the child.'
        for i in range(1, 11)) + '\nSOUVENIR\nFélicitations : Well done!\nPERSONNAGES_JSON\n' + json.dumps({'characters':[
            dict(id='ami_1', name='Sparky', appearance='Yellow creature', pages=list(range(1,11))),
            dict(id='nib', name='Nib', appearance='Silver winglets', pages=[2,3])]})


class CompanionRevisionTests(unittest.TestCase):
    def test_substantive_redesign_preserves_titles_cast_schedule_and_other_companion(self):
        old = existing_story()
        revised = revised_story(old)
        self.assertEqual(revised_story(revised), revised)
        self.assertNotIn('Sparky', revised)
        self.assertNotIn('lightning-shaped', revised)
        self.assertIn(LUMO_APPEARANCE, revised)
        self.assertEqual([p['title'] for p in story_pages(old)], [p['title'] for p in story_pages(revised)])
        cast = json.loads(revised.split('PERSONNAGES_JSON')[1])['characters']
        self.assertEqual(cast[0]['pages'], list(range(1,11)))
        self.assertEqual(cast[1]['appearance'], 'Silver winglets')

    def test_revision_keeps_original_story_and_requires_new_cover_only_once_on_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            story = root/'story.txt'
            story.write_text(existing_story(), encoding='utf-8')
            def cover():
                Path(engine.COVER_FILE).write_bytes(b'new cover')
            engine = SimpleNamespace(STORY_FILE=story, COVER_FILE=root/'old.png',
                atomic_write_bytes=lambda p,d: Path(p).write_bytes(d), generate_cover=MagicMock(side_effect=cover))
            prepare_revision(engine, root, 'English')
            self.assertEqual((root/'story_before_companion_revision.txt').read_text(encoding='utf-8'), existing_story())
            self.assertEqual(Path(engine.COVER_FILE).name, 'cover_lumo_v1.png')
            (root/'pages').mkdir()
            (root/'pages'/'page_01.png').write_bytes(b'revised illustration')
            prepare_revision(engine, root, 'English')
            engine.generate_cover.assert_called_once()

    def test_preexisting_illustrations_and_unreviewed_descriptions_block_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'pages').mkdir()
            (root/'pages'/'page_01.png').write_bytes(b'old art')
            story = root/'story.txt'
            story.write_text(existing_story(), encoding='utf-8')
            engine = SimpleNamespace(STORY_FILE=story, generate_cover=MagicMock())
            with self.assertRaises(ValueError):
                prepare_revision(engine, root, 'English')
            engine.generate_cover.assert_not_called()
            self.assertEqual(story.read_text(encoding='utf-8'), existing_story())
        with self.assertRaises(ValueError):
            revised_story(existing_story().replace('Sparky lights', 'A yellow creature lights'))
