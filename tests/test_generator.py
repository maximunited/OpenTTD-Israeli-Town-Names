import json
import unittest
from pathlib import Path

from make_english import BASE, decode, generate, read_mapping, strip_comments, TEXT


class GeneratorTests(unittest.TestCase):
    def test_escaped_quotes_and_comments(self):
        source = 'text("כפר חב\\"ד", 1) /* text("ignore", 1) */ // text("ignore2", 1)\n'
        names = [decode(m[1]) for m in TEXT.finditer(strip_comments(source))]
        self.assertEqual(names, ['כפר חב"ד'])

    def test_generation(self):
        source = r'grfid: "ZH\01\01";' + '\ntown_names(real) { { text("עיר", 1) } }\ntown_names { { town_names(real, 1) } }'
        output = generate(source, {'עיר': 'Town'})
        self.assertIn(r'grfid: "ZH\01\02";', output)
        self.assertIn('text("Town", 1)', output)
        self.assertIn('town_names(real_english, 1)', output)

    def test_missing_translation_fails(self):
        with self.assertRaises(ValueError):
            generate('text("עיר", 1)', {})

    def test_wrong_id_fails(self):
        with self.assertRaises(ValueError):
            generate('text("עיר", 1)', {'עיר': 'Town'})


    def test_nml_json_escaping(self):
        # English labels with backslashes and double quotes must be escaped for NML.
        source = r'grfid: "ZH\01\01";' + '\ntext("עיר", 1)'
        label = 'Kfar Chabad "Smacha"'
        output = generate(source, {'עיר': label})
        self.assertIn('text("Kfar Chabad \\"Smacha\\"", 1)', output)

    def test_nml_json_escaping_backslash_only(self):
        source = r'grfid: "ZH\01\01";' + '\ntext("עיר", 1)'
        output = generate(source, {'עיר': 'C\\Power'})
        self.assertIn('text("C\\\\Power", 1)', output)

    def test_idempotent_generation(self):
        source = r'grfid: "ZH\01\01";' + '\ntown_names(real) { text("עיר", 1) }'
        output = generate(source, {'עיר': 'Town'})
        self.assertEqual(output, generate(source, {'עיר': 'Town'}))

    def test_write_mapping_round_trip(self):
        path = BASE / 'test_mapping.json'
        data = {'א': 'Amnon', 'ב': 'Beit Zaid'}
        with path.open('w', encoding='utf-8') as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        loaded = read_mapping(path)
        self.assertEqual(loaded, data)
        # duplicate keys must be rejected.
        with path.open('w', encoding='utf-8') as handle:
            json.dump([('א', 'Amnon'), ('א', 'Amnon')], handle)
        with self.assertRaises(ValueError):
            read_mapping(path)
        path.unlink()


if __name__ == '__main__':
    unittest.main()
