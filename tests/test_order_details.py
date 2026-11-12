"""Exercise the production order route without API charges or database writes."""
import ast
import asyncio
import base64
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import json
import re
import unittest
import uuid
from character_identity import IDENTITY_INSTRUCTION


class RequestError(Exception):
    def __init__(self, status_code, detail):
        self.status_code, self.detail = status_code, detail


def production_namespace():
    tree = ast.parse((Path(__file__).parents[1] / "api.py").read_text(encoding="utf-8"))
    names = {"validate_parent_contact", "resolve_order_themes", "save_order_to_supabase", "preview_cover"}
    functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
    for function in functions:
        function.decorator_list = []
    ns = dict(get_pack=__import__("packs").get_pack, IDENTITY_INSTRUCTION=IDENTITY_INSTRUCTION, re=re, json=json, HTTPException=RequestError, Form=lambda default: default,
              File=lambda default: default, UploadFile=object, base64=base64,
              MAX_PHOTO_BYTES=8*1024*1024, datetime=datetime, uuid=uuid, validate_book_style=__import__("book_style").validate_book_style)
    exec(compile(ast.Module(body=functions, type_ignores=[]), "api.py", "exec"), ns)
    return ns


class OrderDetailsTests(unittest.TestCase):
    def setUp(self):
        self.ns = production_namespace()

    def test_required_phone_and_optional_email(self):
        validate = self.ns["validate_parent_contact"]
        self.assertEqual(validate("+212 (612) 345-678", ""), ("+212612345678", ""))
        self.assertEqual(validate("0612345678", " parent@example.com "), ("0612345678", "parent@example.com"))
        for phone, email in [("", ""), ("abc0612345678", ""), ("123", ""), ("0612345678", "bad@"), ("1234567890123456", "")]:
            with self.subTest(phone=phone, email=email), self.assertRaises(RequestError):
                validate(phone, email)

    def test_custom_theme_must_be_described_and_preserves_other_themes(self):
        resolve = self.ns["resolve_order_themes"]
        themes = ["Science", "✨ Mon propre thème"]
        self.assertEqual(resolve(themes, " Un jardin magique "), [("Science", ""), ("Thème personnalisé : Un jardin magique", "Un jardin magique")])
        for idea in ["", "   ", "a"*601]:
            with self.assertRaises(RequestError):
                resolve(themes, idea)
        self.assertEqual(resolve(["Science"]), [("Science", "")])

    def test_route_saves_contact_and_custom_idea_for_the_worker(self):
        class Database:
            def __init__(self): self.storage = self; self.rows = []
            def from_(self, bucket): return self
            def upload(self, *args, **kwargs): pass
            def table(self, name): return self
            def insert(self, row): self.rows.append(row); return self
            def execute(self): pass
        class Photo:
            content_type = "image/png"
            filename = "test.png"
            async def read(self): return b"test"
        db = Database()
        prompts = []
        self.ns.update(get_supabase_client=lambda: db,
            get_openai_client=lambda: SimpleNamespace(images=SimpleNamespace(edit=lambda **kw: SimpleNamespace(data=[SimpleNamespace(b64_json="dGVzdA==")]))),
            image_file=lambda *args: None, gender_instruction=lambda *args: "",
            generate_title=lambda client, name, age, theme, language, gender: prompts.append(theme) or "Test",
            generate_cover=lambda *args: b"test")
        params = dict(child_name="Test", child_age="16 ans", language="Français", theme="", themes=json.dumps(["✨ Mon propre thème"]),
                      photo=Photo(), child_gender="girl", parent_phone="+212 612 345 678", parent_email="", custom_theme="Un jardin magique")
        result = asyncio.run(self.ns["preview_cover"](**params))
        self.assertTrue(result["ok"])
        row = db.rows[0]
        self.assertEqual(row["child_age"], 16)
        self.assertEqual(row["parent_phone"], "+212612345678")
        self.assertIsNone(row["parent_email"])
        self.assertEqual(row["adventures"][0]["idea"], "Un jardin magique")
        self.assertIn("Un jardin magique", prompts[0])
        self.assertEqual(row["total_price"], 79)
        self.assertEqual(row["status"], "WAITING_FOR_PAYMENT")
        self.assertEqual(row["adventures"][0]["book_style"], "coloring")
        params["book_style"] = "colored"
        params["pack_id"] = 3
        asyncio.run(self.ns["preview_cover"](**params))
        self.assertEqual(db.rows[1]["adventures"][0]["book_style"], "colored")
        self.assertEqual(db.rows[1]["total_price"], 199)
        params["parent_phone"] = ""
        self.ns["get_openai_client"] = lambda: self.fail("Invalid contact must fail before paid work")
        with self.assertRaises(RequestError): asyncio.run(self.ns["preview_cover"](**params))
        params["parent_phone"], params["custom_theme"] = "0612345678", ""
        with self.assertRaises(RequestError): asyncio.run(self.ns["preview_cover"](**params))

    def test_all_packs_use_server_prices_and_production_styles(self):
        class Database:
            def __init__(self): self.storage = self; self.rows = []
            def from_(self, bucket): return self
            def upload(self, *args, **kwargs): pass
            def table(self, name): return self
            def insert(self, row): self.rows.append(row); return self
            def execute(self): pass
        class Photo:
            content_type = "image/png"
            filename = "test.png"
            async def read(self): return b"test"
        db = Database()
        title_calls, cover_calls = [], []
        self.ns.update(get_supabase_client=lambda: db,
            get_openai_client=lambda: SimpleNamespace(images=SimpleNamespace(edit=lambda **kw: SimpleNamespace(data=[SimpleNamespace(b64_json="dGVzdA==")]))),
            image_file=lambda *args: None, gender_instruction=lambda *args: "",
            generate_title=lambda *args: title_calls.append(args) or "Test",
            generate_cover=lambda *args: cover_calls.append(args) or b"test")
        from packs import PACKS
        for pack_id, offer in PACKS.items():
            with self.subTest(pack=offer["name"]):
                before_titles, before_covers = len(title_calls), len(cover_calls)
                params = dict(child_name="Test", child_age="7", language="Français",
                    themes=json.dumps(["Science"] * offer["theme_count"]), photo=Photo(),
                    child_gender="boy", parent_phone="0612345678", pack_id=pack_id,
                    book_style="coloring")  # Physical formats must override this client choice.
                asyncio.run(self.ns["preview_cover"](**params))
                row = db.rows[-1]
                self.assertEqual(row["pack"], offer["name"])
                self.assertEqual(row["total_price"], offer["price"])
                self.assertEqual(row["adventure_count"], len(offer["styles"]))
                self.assertEqual([a["book_style"] for a in row["adventures"]], offer["styles"])
                self.assertEqual(row["status"], "WAITING_FOR_PAYMENT")
                self.assertEqual(row["adventures"][0]["digital_copy_included"], pack_id not in (2, 3))
                if pack_id in (4, 5):
                    self.assertEqual(len(title_calls)-before_titles, 1)
                    self.assertEqual(len(cover_calls)-before_covers, 1)
                    first, second = row["adventures"]
                    self.assertEqual(first["title"], second["title"])
                    self.assertEqual(first["theme"], second["theme"])
                    self.assertTrue(second["image_only"])
                    self.assertEqual(second["shared_story_from"], 1)
                    self.assertEqual(second["paired_version"], "same-scenes-v1")
                else:
                    self.assertNotIn("image_only", row["adventures"][0])
        self.ns["get_openai_client"] = lambda: self.fail("Invalid pack must not incur generation cost")
        for pack_id, themes in [(0, ["Science"]), (6, ["Science"]), (4, ["Science", "Nature"]), (1, ["A", "B"]), (5, ["A", "B", "C"])]:
            with self.subTest(pack=pack_id, themes=themes), self.assertRaises(RequestError):
                asyncio.run(self.ns["preview_cover"](child_name="Test", child_age="7", photo=None,
                    child_gender="boy", parent_phone="0612345678", pack_id=pack_id, themes=json.dumps(themes)))

    def test_age_limits_reject_invalid_orders_before_ai_or_photo_processing(self):
        self.ns["get_openai_client"] = lambda: self.fail("Invalid age must not start paid work")
        for age in ("2 ans", "17 ans", "0", "100 ans"):
            with self.subTest(age=age), self.assertRaises(RequestError) as error:
                asyncio.run(self.ns["preview_cover"](child_name="Test", child_age=age,
                    theme="Science", photo=None, child_gender="girl", parent_phone="0612345678"))
            self.assertIn("3 et 16", error.exception.detail)

    def test_digital_cannot_request_a_colored_story(self):
        self.ns["get_openai_client"] = lambda: self.fail("Digital color must fail before paid work")
        with self.assertRaises(RequestError) as error:
            asyncio.run(self.ns["preview_cover"](child_name="Test", child_age="7", theme="Science",
                photo=None, child_gender="boy", parent_phone="0612345678", pack_id=1, book_style="colored"))
        self.assertEqual(error.exception.status_code, 400)
        self.assertIn("Digital", error.exception.detail)

    def test_invalid_book_style_is_rejected_before_any_ai_work(self):
        self.ns["get_openai_client"] = lambda: self.fail("Invalid style must not start paid work")
        with self.assertRaises(RequestError):
            asyncio.run(self.ns["preview_cover"](child_name="Test", child_age="10 ans", theme="Science",
                photo=None, child_gender="boy", parent_phone="0612345678", book_style="unknown"))


if __name__ == "__main__":
    unittest.main()
