import io
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError, URLError
from cbs_http import read_json


def response(body=b'{"ok": true}'):
    result = Mock()
    result.__enter__ = Mock(return_value=result)
    result.__exit__ = Mock(return_value=False)
    result.read.return_value = body
    return result


def http_error(code=500, headers=None):
    return HTTPError('https://example.test', code, 'test failure', headers or {}, io.BytesIO(b'upstream detail'))


class HTTPTests(unittest.TestCase):
    def test_retry_then_success(self):
        opener = Mock(side_effect=[http_error(), response()])
        sleep = Mock()
        self.assertEqual(read_json('https://example.test', opener, sleep), {'ok': True})
        self.assertEqual(opener.call_count, 2)
        sleep.assert_called_once_with(2)

    def test_exhaustion_includes_diagnostics(self):
        opener = Mock(side_effect=[http_error() for _ in range(3)])
        sleep = Mock()
        with self.assertRaisesRegex(RuntimeError, 'upstream detail'):
            read_json('https://example.test', opener, sleep)
        self.assertEqual(opener.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_404_not_retried(self):
        opener, sleep = Mock(side_effect=http_error(404)), Mock()
        with self.assertRaisesRegex(RuntimeError, 'HTTP 404'):
            read_json('https://example.test', opener, sleep)
        self.assertEqual(opener.call_count, 1)
        sleep.assert_not_called()

    def test_retry_after_bounded(self):
        opener, sleep = Mock(side_effect=[http_error(429, {'Retry-After': '600'}), response()]), Mock()
        read_json('https://example.test', opener, sleep)
        sleep.assert_called_once_with(60)

    def test_network_error_retried(self):
        opener, sleep = Mock(side_effect=[URLError('unavailable'), response()]), Mock()
        read_json('https://example.test', opener, sleep)
        sleep.assert_called_once_with(2)

    def test_invalid_json_fails_clearly(self):
        with self.assertRaisesRegex(RuntimeError, 'invalid JSON'):
            read_json('https://example.test', Mock(return_value=response(b'<html>failure</html>')), Mock())

    def test_request_has_user_agent_and_timeout(self):
        opener = Mock(return_value=response())
        read_json('https://example.test', opener, Mock())
        args, kwargs = opener.call_args
        self.assertTrue(args[0].get_header('User-agent'))
        self.assertEqual(kwargs['timeout'], 30)
