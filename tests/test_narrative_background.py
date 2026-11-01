import ast
import base64
from contextlib import ExitStack
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock


class NarrativeBackgroundTests(unittest.TestCase):
    def test_color_book_creates_one_cached_background_and_coloring_creates_none(self):
        tree=ast.parse(Path('generate_book.py').read_text(encoding='utf-8'))
        functions=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)
            and n.name in {'generate_narrative_background','atomic_write_bytes'}],type_ignores=[])
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            (folder/'cover.png').write_bytes(b'cover')
            (folder/'page_01.png').write_bytes(b'first illustration')
            client=MagicMock()
            client.images.edit.return_value=SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(b'background').decode())])
            namespace=dict(Path=Path,base64=base64,ExitStack=ExitStack,BOOK_STYLE='coloring',THEME='Forest',
                COVER_FILE=folder/'cover.png',PAGES_FOLDER=folder,NARRATIVE_BACKGROUND=folder/'background.png',client=client)
            exec(compile(functions,'generate_book.py','exec'),namespace)
            namespace['generate_narrative_background']()
            client.images.edit.assert_not_called()
            namespace['BOOK_STYLE']='colored'
            namespace['generate_narrative_background']()
            self.assertEqual(client.images.edit.call_count,1)
            self.assertEqual((folder/'background.png').read_bytes(),b'background')
            self.assertTrue(all(image.closed for image in client.images.edit.call_args.kwargs['image']))
            self.assertIn('AUCUN personnage',client.images.edit.call_args.kwargs['prompt'])
            namespace['generate_narrative_background']()
            self.assertEqual(client.images.edit.call_count,1)
