import ast
import subprocess
import unittest
from make_english import BASE, HEBREW, TEXT, decode, generate, read_mapping, resolve_translations


class IntegrationTests(unittest.TestCase):
    def test_all_committed_names_resolve(self):
        source = (BASE / 'israel.nml').read_text(encoding='utf-8-sig')
        translations = read_mapping(BASE / 'english_names_cache.json') | read_mapping(BASE / 'english_name_overrides.json') | read_mapping(BASE / 'display_name_preferences.json')
        output = generate(source, translations)
        self.assertTrue(list(TEXT.finditer(output)))
        self.assertFalse(any(HEBREW.search(decode(m[1])) for m in TEXT.finditer(output)))
        self.assertIn('text("Kfar Chabad", 1)', output)
        self.assertIn('text("Givat Haim (Ihud)", 1)', output)
        self.assertEqual(output, generate(source, translations))

    def test_preferences_are_data(self):
        preferences = read_mapping(BASE / 'display_name_preferences.json')
        self.assertEqual(preferences['אמנון'], 'Amnon')
        self.assertEqual(resolve_translations({'a': 'cache'}, {'a': 'override'})['a'], 'override')

    def test_migration_preserves_historical_dictionary(self):
        historical = subprocess.check_output(['git', 'show', '352c8d99bcbd72d0403070d71e94dae2b1c6f9e6:make_english.py'], cwd=BASE).decode('utf-8-sig')
        tree = ast.parse(historical)
        original = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'NAME_OVERRIDES' for target in node.targets))
        self.assertEqual(read_mapping(BASE / 'english_name_overrides.json'), original)

    def test_invalid_translation_rejected(self):
        source = r'grfid: "ZH\01\01";' + '\ntext("עיר", 1)'
        for value in ['', 'עברית', 'bad\nname']:
            with self.assertRaises(ValueError):
                generate(source, {'עיר': value})
