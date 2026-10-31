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


class RequestError(Exception):
    def __init__(self, status_code, detail):
        self.status_code, self.detail = status_code, detail


def production_namespace():
    tree = ast.parse((Path(__file__).parents[1] / "api.py").read_text(encoding="utf-8"))
    names = {"validate_parent_contact", "resolve_order_themes", "save_order_to_supabase", "preview_cover"}
    functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
    for function in functions:
        function.decorator_list = []
    ns = dict(re=re, json=json, HTTPException=RequestError, Form=lambda default: default,
              File=lambda default: default, UploadFile=object, base64=base64,
              MAX_PHOTO_BYTES=8*1024*1024, datetime=datetime, uuid=uuid)
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
        params = dict(child_name="Test", child_age="7 ans", language="Français", theme="", themes=json.dumps(["✨ Mon propre thème"]),
                      photo=Photo(), child_gender="girl", parent_phone="+212 612 345 678", parent_email="", custom_theme="Un jardin magique")
        result = asyncio.run(self.ns["preview_cover"](**params))
        self.assertTrue(result["ok"])
        row = db.rows[0]
        self.assertEqual(row["parent_phone"], "+212612345678")
        self.assertIsNone(row["parent_email"])
        self.assertEqual(row["adventures"][0]["idea"], "Un jardin magique")
        self.assertIn("Un jardin magique", prompts[0])
        self.assertEqual(row["total_price"], 99)
        self.assertEqual(row["status"], "WAITING_FOR_PAYMENT")
        params["parent_phone"] = ""
        self.ns["get_openai_client"] = lambda: self.fail("Invalid contact must fail before paid work")
        with self.assertRaises(RequestError): asyncio.run(self.ns["preview_cover"](**params))
        params["parent_phone"], params["custom_theme"] = "0612345678", ""
        with self.assertRaises(RequestError): asyncio.run(self.ns["preview_cover"](**params))


if __name__ == "__main__":
    unittest.main()
