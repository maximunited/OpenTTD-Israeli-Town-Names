import csv
import tempfile
import unittest
from pathlib import Path

from make_english import label_origin, source_names, write_candidates_csv, write_review_csv


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.reader(handle))


def record(code, hebrew, english='NAME', locality_type='310'):
    return {'id': code, 'year': '2024', 'name_heb': hebrew, 'name_eng': english, 'locality_type': locality_type}


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_source_names_dedupes_and_skips_comments(self):
        source = 'text("א", 1)\n// text("ב", 1)\ntext("א", 2)\ntext("ג", 1)'
        self.assertEqual(source_names(source), ['א', 'ג'])

    def test_label_origin_uses_first_matching_layer(self):
        layers = [('preference', {'א': 'A'}), ('override', {'א': 'B', 'ב': 'C'})]
        self.assertEqual(label_origin('א', layers), 'preference')
        self.assertEqual(label_origin('ב', layers), 'override')
        self.assertEqual(label_origin('ג', layers), 'UNRESOLVED')

    def test_review_csv_sorted_by_english(self):
        path = self.root / 'review.csv'
        translations = {'א': 'zeta', 'ב': 'Alpha'}
        write_review_csv(path, ['א', 'ב', 'ג'], translations, [('cache', translations)])
        self.assertEqual(read_csv(path), [
            ['hebrew', 'english', 'source'],
            ['ג', '', 'UNRESOLVED'],
            ['ב', 'Alpha', 'cache'],
            ['א', 'zeta', 'cache'],
        ])

    def test_candidates_list_only_missing_towns(self):
        path = self.root / 'candidates.csv'
        records = [
            record('1', 'תל אביב'),
            record('2', 'אזור תעשייה הר-טוב', locality_type='520'),
            record('3', 'יישוב חדש', "'NEW  TOWN"),
            record('4', 'ללא אנגלית', None),
            record('5', 'אבו עמרה (שבט)', locality_type='460'),
            record('6', 'הרי יהודה מ"א 26', locality_type='530'),
            record('7', 'מחנה הילה*', locality_type='510'),
        ]
        write_candidates_csv(path, records, ['תל אביב'])
        self.assertEqual(read_csv(path), [
            ['id', 'year', 'locality_type', 'hebrew', 'english'],
            ['3', '2024', '310', 'יישוב חדש', 'NEW TOWN'],
            ['4', '2024', '310', 'ללא אנגלית', ''],
        ])


if __name__ == '__main__':
    unittest.main()
