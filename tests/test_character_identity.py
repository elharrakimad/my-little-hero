import ast
import base64
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from character_identity import IDENTITY_INSTRUCTION


class CharacterIdentityTests(unittest.TestCase):
    def test_cover_uses_same_identity_rule_for_every_theme(self):
        tree = ast.parse(Path('api.py').read_text(encoding='utf-8'))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'generate_cover')
        namespace = dict(IDENTITY_INSTRUCTION=IDENTITY_INSTRUCTION, base64=base64,
            image_file=lambda data, name: data, cover_subtitle=lambda *args: 'Livre',
            gender_instruction=lambda *args: '', visual_reference_instruction=lambda theme: theme,
            anime_cast_instruction=lambda *args: '')
        exec(compile(ast.Module(body=[function], type_ignores=[]), 'api.py', 'exec'), namespace)
        client = MagicMock()
        client.images.edit.return_value = SimpleNamespace(data=[SimpleNamespace(b64_json='aW1hZ2U=')])
        for theme in ('Science', 'Princesse', 'Inspirations anime', 'Thème personnalisé'):
            for style in ('colored', 'coloring'):
                namespace['generate_cover'](client, b'initial reference', 'Salima', 16,
                    theme, 'Español', 'Salima', 'girl', style)
                request = client.images.edit.call_args.kwargs
                self.assertEqual(request['image'][0], b'initial reference')
                self.assertIn(IDENTITY_INSTRUCTION, request['prompt'])
