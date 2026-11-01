import ast
import base64
import contextlib
import io
from pathlib import Path
import runpy
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from book_style import validate_book_style, book_output_dir, illustration_direction, cover_subtitle
from book_layout import souvenir_copy, paragraph, DEFAULT_LAYOUT
import character_continuity as continuity
import anime_cast


class BookStyleTests(unittest.TestCase):
    def test_default_is_coloring_and_color_cache_is_separate(self):
        self.assertEqual(validate_book_style(), 'coloring')
        self.assertEqual(book_output_dir('book'), Path('book'))
        self.assertEqual(book_output_dir('book','colored'), Path('book/colored'))
        with self.assertRaises(ValueError): validate_book_style('invalid')

    def test_colored_instructions_keep_outfit_colors_and_never_request_monochrome(self):
        color = illustration_direction('colored',16)
        self.assertIn('entièrement colorée',color)
        self.assertNotIn('aucun remplissage',color)
        self.assertIn('noir et blanc',illustration_direction('coloring',7).lower())
        self.assertNotIn('zones blanches à colorier',continuity.child_outfit_instruction('colored'))
        for lang in ('Français','English','Español','العربية'):
            self.assertNotEqual(cover_subtitle(lang,'colored'),cover_subtitle(lang,'coloring'))
            self.assertNotEqual(souvenir_copy('Itar',language=lang,book_style='colored')[2], souvenir_copy('Itar',language=lang)[2])
            copy=souvenir_copy('Itar',language=lang,book_style='colored')
            self.assertLessEqual(paragraph(copy[2],centered=True).wrap(DEFAULT_LAYOUT.content_width-36,1000)[1],40)
            self.assertLessEqual(paragraph(copy[3],size=20,leading=25,title=True).wrap(DEFAULT_LAYOUT.content_width,1000)[1],28)

    def test_style_resets_between_orders_and_caches_never_mix(self):
        engine=MagicMock()
        engine.get_book_title.side_effect=lambda:engine.BOOK_TITLE
        engine.generate_pdf.side_effect=lambda:Path(engine.OUTPUT_FILE).write_bytes(b'pdf')
        with patch.dict('sys.modules',{'generate_book':engine}):
            wrapper=runpy.run_path('book_engine.py')['generate_book_from_adventure']
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            paths=[]
            for style in ('colored','coloring'):
                paths.append(wrapper(child_name='Itar',age=12,theme='Science',language='Français',client_idea='',
                    child_quality='',book_title='Aventure',reference_path='reference.png',output_dir=folder,book_style=style))
                self.assertEqual(engine.BOOK_STYLE,style)
            self.assertNotEqual(paths[0],paths[1])
            self.assertTrue(all(p.is_file() for p in paths))

    def test_actual_page_requests_use_selected_style(self):
        tree=ast.parse(Path('generate_book.py').read_text(encoding='utf-8'))
        names={'generate_page','extract_scene','extract_title','require_file','atomic_write_bytes'}
        functions=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
        for style in ('coloring','colored'):
            with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
                folder=Path(folder)
                for name in ('child.png','cover.png'): (folder/name).write_bytes(b'image')
                (folder/'story.txt').write_text('PAGE 1\nTitre : Aventure\nTexte : Itar découvre une forêt.\nScène à illustrer : Itar seul.\nSOUVENIR\nFélicitations : Bravo !\nPERSONNAGES_JSON\n{"characters":[]}',encoding='utf-8')
                client=MagicMock()
                client.images.edit.return_value=SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(b'image').decode())])
                ns=dict(Path=Path,re=__import__('re'),base64=base64,ExitStack=contextlib.ExitStack,
                    gender_instruction=__import__('child_profile').gender_instruction,
                    visual_reference_instruction=__import__('story_reference').visual_reference_instruction,
                    illustration_direction=illustration_direction,continuity_context=continuity.continuity_context,
                    page_composition=__import__('book_style').page_composition,
                    reference_paths=continuity.reference_paths,reference_roles=continuity.reference_roles,
                    secondary_reference_folder=anime_cast.secondary_reference_folder,anime_cast_instruction=anime_cast.anime_cast_instruction,
                    client=client,CHILD_GENDER='boy',AGE=12,THEME='Science',BOOK_STYLE=style,NUMBER_OF_PAGES=10,
                    PAGES_FOLDER=folder,STORY_FILE=folder/'story.txt',COVER_FILE=folder/'cover.png',REFERENCE_IMAGE=folder/'child.png',REUSE_EXISTING_FILES=True)
                exec(compile(functions,'generate_book.py','exec'),ns)
                ns['generate_page'](1,'Titre : Aventure\nScène à illustrer : Itar seul.')
                prompt=client.images.edit.call_args.kwargs['prompt']
                self.assertIn(illustration_direction(style,12),prompt)
                if style=='colored':
                    self.assertNotIn('zones blanches à colorier',prompt)
                    self.assertNotIn('en contours noirs sur fond blanc',prompt)
                self.assertEqual(client.images.edit.call_count,1)
