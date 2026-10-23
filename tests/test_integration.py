from pathlib import Path
import ast
import subprocess
import unittest

from make_english import BASE, HEBREW, TEXT, decode, generate, read_mapping, resolve_translations


class IntegrationTests(unittest.TestCase):
    def test_all_committed_names_resolve(self):
        source = (BASE / 'israel.nml').read_text(encoding='utf-8-sig')
        cache = read_mapping(BASE / 'english_names_cache.json')
        overrides = read_mapping(BASE / 'english_name_overrides.json')
        output = generate(source, resolve_translations(cache, overrides))
        self.assertTrue(list(TEXT.finditer(output)))
        self.assertFalse(any(HEBREW.search(decode(m[1])) for m in TEXT.finditer(output)))
        self.assertIn('text("Kfar Chabad", 1)', output)
        self.assertIn('text("Givat Haim (Ihud)", 1)', output)

    def test_amnon_and_override_priority(self):
        self.assertEqual(resolve_translations({'אמנון': 'Amnun'}, {}, True)['אמנון'], 'Amnon')
        self.assertEqual(resolve_translations({'a': 'cache'}, {'a': 'override'})['a'], 'override')

    def test_migration_preserves_historical_dictionary(self):
        historical = subprocess.check_output(['git', 'show', '352c8d99bcbd72d0403070d71e94dae2b1c6f9e6:make_english.py'], cwd=BASE).decode('utf-8-sig')
        tree = ast.parse(historical)
        original = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'NAME_OVERRIDES' for target in node.targets))
        self.assertEqual(read_mapping(BASE / 'english_name_overrides.json'), original)


if __name__ == '__main__':
    unittest.main()
