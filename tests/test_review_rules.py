import unittest
from review_rules import classify_candidate, normalize_english_label, resolve_mapping, validate_english_label


def row(hebrew, english='NAME'):
    return {'id': '1', 'year': '2024', 'name_heb': hebrew, 'name_eng': english}


class ClassificationTests(unittest.TestCase):
    def test_exact_playable_match(self):
        self.assertEqual(classify_candidate(row('תל אביב'), {'תל אביב'}), 'EXACT PLAYABLE MATCH')

    def test_tribe_is_not_a_town(self):
        self.assertEqual(classify_candidate(row('תראבין א-צאנע (שבט)'), set()), 'NOT A TOWN: REVIEW ELIGIBILITY')

    def test_industrial_zone_is_not_a_town(self):
        self.assertEqual(classify_candidate(row('אזור תעשייה הר-טוב'), set()), 'NOT A TOWN: REVIEW ELIGIBILITY')

    def test_hospital_is_not_a_town(self):
        self.assertEqual(classify_candidate(row('בית חולים פוריה'), set()), 'NOT A TOWN: REVIEW ELIGIBILITY')

    def test_school_is_not_a_town(self):
        self.assertEqual(classify_candidate(row('בי"ס אזורי מקיף (אשר)'), set()), 'NOT A TOWN: REVIEW ELIGIBILITY')

    def test_unmatched_settlement_needs_alias_review(self):
        self.assertEqual(classify_candidate(row('תראבין א-צאנע (יישוב)'), set()), 'NOT EXACTLY MATCHED: REVIEW ALIAS/ELIGIBILITY')


class MappingTests(unittest.TestCase):
    def test_preference_wins(self):
        result = resolve_mapping({'א': 'CBS'}, {'א': 'CACHE'}, {'א': 'OVERRIDE'}, {'א': 'PREFERENCE'})
        self.assertEqual(result['א'], 'PREFERENCE')

    def test_override_beats_cache_and_cbs(self):
        result = resolve_mapping({'א': 'CBS'}, {'א': 'CACHE'}, {'א': 'OVERRIDE'}, {})
        self.assertEqual(result['א'], 'OVERRIDE')

    def test_cache_beats_cbs(self):
        result = resolve_mapping({'א': 'CBS'}, {'א': 'CACHE'}, {}, {})
        self.assertEqual(result['א'], 'CACHE')

    def test_duplicate_within_merge_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate Hebrew mapping'):
            resolve_mapping({'א': 'CBS'}, {'א': 'CACHE'}, {}, {})

    def test_invalid_english_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Hebrew characters'):
            resolve_mapping({'א': 'עברית'}, {}, {}, {})

    def test_empty_english_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Empty English label'):
            resolve_mapping({'א': '   '}, {}, {}, {})


class LabelTests(unittest.TestCase):
    def test_leading_apostrophe_normalized(self):
        self.assertEqual(normalize_english_label("'TARABIN AS-SANI"), 'TARABIN AS-SANI')

    def test_internal_apostrophe_preserved(self):
        self.assertEqual(normalize_english_label("MA'YAN ZEVI"), "MA'YAN ZEVI")

    def test_whitespace_normalized(self):
        self.assertEqual(normalize_english_label('  ABU  AMMAR  '), 'ABU AMMAR')

    def test_non_text_rejected(self):
        with self.assertRaises(ValueError):
            normalize_english_label(None)
