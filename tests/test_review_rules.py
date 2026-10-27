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

    def test_district_is_not_a_town(self):
        self.assertEqual(classify_candidate(row("נפת ג'נין"), set()), 'NOT A TOWN: REVIEW ELIGIBILITY')

    def test_military_camp_is_not_a_town(self):
        self.assertEqual(classify_candidate(row('מחנה הילה*'), set()), 'NOT A TOWN: REVIEW ELIGIBILITY')

    def test_industrial_park_is_not_a_town(self):
        self.assertEqual(classify_candidate(row('פארק תעשיות עמק חפר'), set()), 'NOT A TOWN: REVIEW ELIGIBILITY')

    def test_regional_statistical_area_is_not_a_town(self):
        self.assertEqual(classify_candidate(row('גמ"ל מחוז דרום'), set()), 'NOT A TOWN: REVIEW ELIGIBILITY')

    def test_dead_sea_hotels_are_not_a_town(self):
        self.assertEqual(classify_candidate(row('ים המלח - בתי מלון'), set()), 'NOT A TOWN: REVIEW ELIGIBILITY')

    def test_trailing_asterisk_is_not_a_town(self):
        self.assertEqual(classify_candidate(row('אילון תבור*'), set()), 'NOT A TOWN: REVIEW ELIGIBILITY')

    def test_potential_town_stays_for_alias_review(self):
        self.assertEqual(classify_candidate(row('טובא-זנגרייה'), set()), 'NOT EXACTLY MATCHED: REVIEW ALIAS/ELIGIBILITY')

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

    def test_invalid_english_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Hebrew characters'):
            resolve_mapping({'א': 'עברית'}, {}, {}, {})

    def test_empty_english_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Empty English label'):
            resolve_mapping({'א': '   '}, {}, {}, {})

    def test_resolution_order_preference_override_cache_cbs(self):
        cbs = {'א': 'CBS_VALUE'}
        cache = {'א': 'CACHE_VALUE'}
        override = {'א': 'OVERRIDE_VALUE'}
        preferences = {'א': 'PREFERENCE_VALUE'}
        result = resolve_mapping(cbs, cache, override, preferences)
        self.assertEqual(result['א'], 'PREFERENCE_VALUE')

    def test_resolution_no_preference_keeps_override(self):
        cbs = {'א': 'CBS_VALUE'}
        cache = {'א': 'CACHE_VALUE'}
        override = {'א': 'OVERRIDE_VALUE'}
        result = resolve_mapping(cbs, cache, override, {})
        self.assertEqual(result['א'], 'OVERRIDE_VALUE')

    def test_resolution_empty_layers_drop(self):
        result = resolve_mapping({}, {}, {}, {})
        self.assertEqual(result, {})

    def test_invalid_layer_raises(self):
        with self.assertRaisesRegex(ValueError, 'CBS mapping must be a dictionary'):
            resolve_mapping('not a dict', {}, {}, {})



class LabelTests(unittest.TestCase):
    def test_leading_apostrophe_normalized(self):
        self.assertEqual(normalize_english_label("'TARABIN AS-SANI"), 'TARABIN AS-SANI')

    def test_internal_apostrophe_preserved(self):
        self.assertEqual(normalize_english_label("MA'YAN ZEVI"), "MA'YAN ZEVI")

    def test_whitespace_normalized(self):
        self.assertEqual(normalize_english_label('  ABU  AMMAR  '), 'ABU AMMAR')

    def test_missing_space_before_parenthesis_added(self):
        self.assertEqual(normalize_english_label('MERHAVYA(QIBBUZ)'), 'MERHAVYA (QIBBUZ)')
        self.assertEqual(normalize_english_label("BEN SHEMEN(K.NO'AR)"), "BEN SHEMEN (K.NO'AR)")

    def test_existing_space_before_parenthesis_preserved(self):
        self.assertEqual(normalize_english_label("TAMRA (YIZRE'EL)"), "TAMRA (YIZRE'EL)")

    def test_non_text_rejected(self):
        with self.assertRaises(ValueError):
            normalize_english_label(None)

    def test_normalize_leading_apostrophe(self):
        self.assertEqual(normalize_english_label("'TARABIN AS-SANI"), 'TARABIN AS-SANI')

    def test_normalize_internal_apostrophe_preserved(self):
        self.assertEqual(normalize_english_label("MA'YAN ZEVI"), "MA'YAN ZEVI")

    def test_normalize_whitespace(self):
        self.assertEqual(normalize_english_label('  ABU  AMMAR  '), 'ABU AMMAR')

    def test_normalize_missing_space_before_parenthesis(self):
        self.assertEqual(normalize_english_label('MERHAVYA(QIBBUZ)'), 'MERHAVYA (QIBBUZ)')
        self.assertEqual(normalize_english_label("BEN SHEMEN(K.NO'AR)"), "BEN SHEMEN (K.NO'AR)")

    def test_normalize_existing_space_before_parenthesis_preserved(self):
        self.assertEqual(normalize_english_label("TAMRA (YIZRE'EL)"), "TAMRA (YIZRE'EL)")

    def test_normalize_trailing_apostrophe(self):
        self.assertEqual(normalize_english_label("TARABIN AS-SANI'"), 'TARABIN AS-SANI')

    def test_normalize_non_string_raises(self):
        with self.assertRaises(ValueError):
            normalize_english_label(123)

    def test_normalize_no_double_space(self):
        self.assertEqual(normalize_english_label('A  B'), 'A B')

    def test_validate_english_label_empty(self):
        with self.assertRaisesRegex(ValueError, 'Empty English label'):
            validate_english_label('   ')

    def test_validate_english_label_hebrew_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Hebrew characters'):
            validate_english_label('English עברית')

    def test_validate_english_label_control_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Control characters'):
            validate_english_label('bad\x00name')

    def test_validate_english_label_ok(self):
        self.assertEqual(validate_english_label("MA'YAN ZEVI"), "MA'YAN ZEVI")

    def test_validate_returns_normalized(self):
        self.assertEqual(validate_english_label("'  ABU  AMMAR  '"), 'ABU AMMAR')

