import unittest
from cbs_pagination import collect_pages


class PaginationTests(unittest.TestCase):
    def fetch(self, pages):
        calls = []
        def read(page, year):
            calls.append(page)
            if page > len(pages):
                raise RuntimeError('unexpected request or HTTP 500')
            values = pages[page - 1]
            if isinstance(values, Exception):
                raise values
            return [{'id': str(value), 'year': '2024'} for value in values]
        return read, calls

    def test_partial_final(self):
        read, calls = self.fetch([[1, 2], [3]])
        self.assertEqual(len(collect_pages(None, read, lambda x: x, page_size=2)), 3)
        self.assertEqual(calls, [1, 2])

    def test_exact_full(self):
        read, calls = self.fetch([[1, 2], [3, 4], []])
        self.assertEqual(len(collect_pages(None, read, lambda x: x, page_size=2)), 4)
        self.assertEqual(calls, [1, 2, 3])

    def test_server_error_propagates(self):
        read, _ = self.fetch([[1, 2], RuntimeError('HTTP 500')])
        with self.assertRaisesRegex(RuntimeError, 'HTTP 500'):
            collect_pages(None, read, lambda x: x, page_size=2)

    def test_short_initial_not_assumed_complete(self):
        read, calls = self.fetch([[1], [2], []])
        self.assertEqual(len(collect_pages(None, read, lambda x: x, page_size=2)), 2)
        self.assertEqual(calls, [1, 2, 3])

    def test_duplicate_rejected(self):
        read, _ = self.fetch([[1, 2], [2]])
        with self.assertRaises(ValueError):
            collect_pages(None, read, lambda x: x, page_size=2)

    def test_oversized_rejected(self):
        read, _ = self.fetch([[1, 2, 3]])
        with self.assertRaises(ValueError):
            collect_pages(None, read, lambda x: x, page_size=2)
