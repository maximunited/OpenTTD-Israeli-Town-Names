import json
import tempfile
import unittest
from pathlib import Path

from make_english import decode, encode, generate, read_mapping, strip_comments, TEXT


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
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test_mapping.json'
            data = {'א': 'Amnon', 'ב': 'Beit Zaid'}
            with path.open('w', encoding='utf-8') as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
            loaded = read_mapping(path)
            self.assertEqual(loaded, data)
            path.write_text('{"א": "Amnon", "א": "Other"}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'duplicate key'):
                read_mapping(path)


    def test_strip_block_comment(self):
        self.assertEqual(strip_comments('a /* hidden */ b'), 'a  b')

    def test_strip_line_comment(self):
        self.assertEqual(strip_comments('a // hidden\nb'), 'a \nb')

    def test_strip_preserves_strings(self):
        self.assertEqual(strip_comments('"/* not a comment */"'), '"/* not a comment */"')

    def test_strip_multiline_block_preserves_line_count(self):
        result = strip_comments('a\n/* line1\nline2 */\nb')
        self.assertEqual(result.count('\n'), 3)

    def test_encode_decode_round_trip(self):
        for value in ['plain', 'with "quotes"', 'back\\slash', 'both\\"mixed']:
            self.assertEqual(decode(encode(value)), value)

    def test_duplicate_names_deduplicated(self):
        source = r'grfid: "ZH\01\01";' + '\ntext("עיר", 1)\ntext("עיר", 1)'
        output = generate(source, {'עיר': 'Town'})
        self.assertEqual(output.count('text("Town", 1)'), 2)

    def test_no_names_raises(self):
        source = r'grfid: "ZH\01\01";' + '\n// no names'
        with self.assertRaisesRegex(ValueError, 'No town names found'):
            generate(source, {})

    def test_read_mapping_missing_file(self):
        self.assertEqual(read_mapping(Path('/nonexistent/path.json')), {})

    def test_read_mapping_rejects_non_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.json'
            path.write_text('["a list"]', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'expected a JSON object'):
                read_mapping(path)

    def test_read_mapping_rejects_hebrew_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.json'
            path.write_text('{"א": "עברית"}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'invalid English translation'):
                read_mapping(path)


if __name__ == '__main__':
    unittest.main()
