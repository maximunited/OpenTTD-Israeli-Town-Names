import json
from pathlib import Path
import tempfile
import unittest
from cbs_directory import fetch_snapshot, parse_page, refresh, translations_from_snapshot


def payload(rows):
    return {'dictionary': {'code': '200', 'data': {'localities': {'items': [{'localities': row} for row in rows]}}}}


def record(code='1', year='2024', hebrew='עיר'):
    return {'ID': {'id': code, 'year': year}, 'name_heb': hebrew, 'name_eng': 'Town'}


class CBSTests(unittest.TestCase):
    def test_pagination(self):
        calls = []
        def page(number, year):
            calls.append(number)
            return payload([record(str(number))] if number < 3 else [])
        result = fetch_snapshot(fetch_page=page, minimum_records=2)
        self.assertEqual(calls, [1, 2, 3])
        self.assertEqual(len(result['records']), 2)

    def test_repeated_page(self):
        with self.assertRaises(ValueError):
            fetch_snapshot(fetch_page=lambda *args: payload([record()]), minimum_records=1)

    def test_mixed_years(self):
        def page(number, year):
            return payload([record('1'), record('2', '2025')] if number == 1 else [])
        with self.assertRaises(ValueError):
            fetch_snapshot(fetch_page=page, minimum_records=1)

    def test_bad_schema(self):
        for value in [{}, {'dictionary': {'code': '500'}}, payload([{}])]:
            with self.assertRaises(ValueError):
                parse_page(value)

    def test_failed_refresh_preserves_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'snapshot.json'
            original = json.dumps({'records': []})
            path.write_text(original)
            with self.assertRaises(ValueError):
                refresh(path, fetch_page=lambda *args: payload([]))
            self.assertEqual(path.read_text(), original)

    def test_ambiguous_hebrew_not_used(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'snapshot.json'
            rows = [{'name_heb': 'עיר', 'name_eng': 'A'}, {'name_heb': 'עיר', 'name_eng': 'B'}]
            path.write_text(json.dumps({'records': rows}))
            self.assertEqual(translations_from_snapshot(path), {})
