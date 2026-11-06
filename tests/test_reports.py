import csv
import json
import tempfile
import unittest
from pathlib import Path

from make_english import label_origin, read_exclusions, source_names, write_candidates_csv, write_review_csv


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.reader(handle))


def record(code, hebrew, english='NAME'):
    return {'id': code, 'year': '2024', 'name_heb': hebrew, 'name_eng': english}


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

    def test_candidates_skip_playable_and_apply_exclusions(self):
        path = self.root / 'candidates.csv'
        records = [
            record('1', 'תל אביב'),
            record('2', 'אזור תעשייה'),
            record('3', 'יישוב חדש', "'NEW  TOWN"),
            record('4', 'ללא אנגלית', None),
        ]
        write_candidates_csv(path, records, ['תל אביב'], {'2': {'reason': 'industrial zone'}})
        rows = read_csv(path)
        self.assertEqual([row[0] for row in rows[1:]], ['2', '3', '4'])
        self.assertEqual(rows[1][4], 'EXCLUDED: industrial zone')
        self.assertEqual(rows[2][3], 'NEW TOWN')
        self.assertEqual(rows[2][4], 'NOT EXACTLY MATCHED: REVIEW ALIAS/ELIGIBILITY')
        self.assertEqual(rows[3][3], '')

    def test_read_exclusions_missing_file(self):
        self.assertEqual(read_exclusions(self.root / 'missing.json'), {})

    def test_read_exclusions_rejects_bad_entries(self):
        path = self.root / 'exclusions.json'
        for bad in [[], {'abc': {'reason': 'x'}}, {'1': 'x'}, {'1': {}}, {'1': {'reason': ' '}}]:
            path.write_text(json.dumps(bad), encoding='utf-8')
            with self.assertRaises(ValueError, msg=bad):
                read_exclusions(path)

    def test_committed_exclusions_are_valid(self):
        from make_english import BASE
        self.assertTrue(read_exclusions(BASE / 'data' / 'cbs_exclusions.json'))


if __name__ == '__main__':
    unittest.main()
