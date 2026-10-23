import unittest
from make_english import normalize_english_label


class NormalizeEnglishTests(unittest.TestCase):
    def test_removes_leading_artifact(self):
        self.assertEqual(normalize_english_label("'TARABIN AS-SANI"), 'TARABIN AS-SANI')

    def test_preserves_internal_apostrophe(self):
        self.assertEqual(normalize_english_label("MA'YAN ZEVI"), "MA'YAN ZEVI")

    def test_removes_trailing_artifact(self):
        self.assertEqual(normalize_english_label("TARABIN AS-SANI'"), 'TARABIN AS-SANI')

    def test_trims_and_collapses_whitespace(self):
        self.assertEqual(normalize_english_label('  ABU  AMMAR  '), 'ABU AMMAR')

    def test_rejects_non_text(self):
        with self.assertRaises(ValueError):
            normalize_english_label(None)
