"""Bounded CBS HTTP retries and diagnostics; no data-source substitution."""
import json
import logging
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LOG = logging.getLogger(__name__)
USER_AGENT = 'OpenTTD-Israeli-Town-Names/1.0 (github.com/maximunited/OpenTTD-Israeli-Town-Names)'


def read_json(url, opener=None, sleep=None, attempts=3):
    opener = opener or urlopen
    sleep = sleep or time.sleep
    request = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    for attempt in range(attempts):
        LOG.warning('CBS request attempt %s/%s: %s', attempt + 1, attempts, url)
        try:
            with opener(request, timeout=30) as response:
                raw = response.read()
                try:
                    return json.loads(raw)
                except (ValueError, UnicodeError) as error:
                    raise RuntimeError(f'CBS returned invalid JSON for {url}; body prefix={raw[:1024]!r}') from error
        except HTTPError as error:
            try:
                body = error.read(2048).decode('utf-8', errors='replace')
                headers = {key: error.headers.get(key) for key in ('Content-Type', 'Retry-After', 'Server', 'Date') if error.headers and error.headers.get(key)}
                detail = f'HTTP {error.code}; headers={headers}; body prefix={body!r}'
                retry_after = error.headers.get('Retry-After') if error.headers else None
            finally:
                error.close()
            retryable = error.code == 429 or 500 <= error.code < 600
        except (URLError, TimeoutError, ConnectionError) as error:
            detail = f'{type(error).__name__}: {error}'
            retry_after = None
            retryable = True
        LOG.warning('CBS request failed: %s', detail)
        if not retryable or attempt + 1 == attempts:
            raise RuntimeError(f'CBS download failed for {url} after {attempt + 1} attempt(s): {detail}. Existing snapshot is not replaced.')
        delay = min(60, int(retry_after)) if retry_after and retry_after.isdigit() else 2 ** (attempt + 1)
        LOG.warning('Retrying CBS in %s seconds', delay)
        sleep(delay)


def diagnose():
    from urllib.parse import urlencode
    base = 'https://api.cbs.gov.il/Dictionary/geo/localities'
    variants = [({}, 'minimal endpoint'), ({'format': 'json', 'download': 'false', 'page': 1, 'page_size': 50}, 'documented small page'), ({'format': 'json', 'expand': 'false', 'page': 1, 'page_size': 250}, 'production request')]
    for params, label in variants:
        url = base + ('?' + urlencode(params) if params else '')
        print(f'PROBE {label}: {url}', flush=True)
        try:
            payload = read_json(url, attempts=1)
            print(f'JSON response type: {type(payload).__name__}; keys: {list(payload)[:10] if isinstance(payload, dict) else "not an object"}', flush=True)
        except Exception as error:
            print(f'PROBE FAILED: {error}', flush=True)
    print('Diagnostic probes do not write snapshots and do not establish dataset completeness.', flush=True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    diagnose()
