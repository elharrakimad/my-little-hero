import unittest

from story_reference import visual_reference_instruction


class StoryReferenceTests(unittest.TestCase):
    def test_detailed_reference_keeps_supplied_details_and_child_identity(self):
        direction = visual_reference_instruction(
            "Héros personnalisé : agilité. Tenue et apparence : combinaison rouge et bleue. "
            "Adversaires ou obstacles : un farceur et une énigme."
        )
        self.assertIn("Ne pas remplacer", direction)
        self.assertIn("L'enfant reste le personnage principal", direction)
        self.assertIn("sans reprendre un scénario existant", direction)
        self.assertIn("sans blessure ni sang", direction)

    def test_general_themes_keep_original_characters_and_worlds(self):
        direction = visual_reference_instruction("Une aventure de pirates")
        self.assertIn("totalement originaux", direction)
        self.assertNotIn("fiche de référence", direction)


if __name__ == "__main__":
    unittest.main()
