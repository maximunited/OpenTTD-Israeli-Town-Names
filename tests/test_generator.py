import unittest
from make_english import decode, generate, strip_comments, TEXT


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


if __name__ == '__main__':
    unittest.main()
