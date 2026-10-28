import ast
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from child_profile import gender_instruction


class ProfileTests(unittest.TestCase):
    def api_functions(self, **extra):
        tree = ast.parse(Path("api.py").read_text(encoding="utf-8"))
        names = {"generate_title", "save_order_to_supabase", "language_instruction"}
        namespace = {"gender_instruction": gender_instruction, **extra}
        functions = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[])
        exec(compile(functions, "api.py", "exec"), namespace)
        return namespace

    def test_title_receives_gender_and_language(self):
        for gender, expected in [("girl", "une fille"), ("boy", "un garçon")]:
            client = MagicMock()
            client.responses.create.return_value = SimpleNamespace(output_text="Un titre")
            functions = self.api_functions()
            functions["generate_title"](client, "Camille", 7, "Espace", "Español", gender)
            prompt = client.responses.create.call_args.kwargs["input"]
            self.assertIn(expected, prompt)
            self.assertIn("español", prompt)
            self.assertIn("participes", prompt)

    def test_gender_survives_order_storage(self):
        db = MagicMock()
        functions = self.api_functions(get_supabase_client=lambda: db)
        functions["save_order_to_supabase"]("TEST", "Camille", 7, "Français", 1,
            [{"title": "Titre", "theme": "Espace"}], b"reference", [b"cover"], "girl")
        order = db.table.return_value.insert.call_args.args[0]
        self.assertEqual(order["adventures"][0]["child_gender"], "girl")

    def test_legacy_orders_do_not_infer_gender(self):
        self.assertIn("ne pas le déduire", gender_instruction(""))


if __name__ == "__main__":
    unittest.main()
