"""Fetch a complete CBS locality snapshot; never silently alter the playable list."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import time

URL = 'https://api.cbs.gov.il/Dictionary/geo/localities'
PAGE_SIZE = 250


def request_page(page, year=None):
    params = {'format': 'json', 'expand': 'false', 'page': page, 'page_size': PAGE_SIZE}
    if year is not None:
        params['year'] = year
    request = Request(URL + '?' + urlencode(params), headers={'User-Agent': 'OpenTTD-Israeli-Town-Names/1.0 (github.com/maximunited/OpenTTD-Israeli-Town-Names)', 'Accept': 'application/json'})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code != 429 and error.code < 500:
                raise
            if attempt == 2:
                raise
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(2 ** attempt)


def parse_page(payload):
    try:
        dictionary = payload['dictionary']
        if str(dictionary['code']) != '200':
            raise ValueError('CBS returned a non-success code')
        items = dictionary['data']['localities']['items']
    except (KeyError, TypeError) as error:
        raise ValueError('Unexpected CBS response schema') from error
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        raise ValueError('CBS items must be a list or record')
    records = []
    for item in items:
        try:
            row = item['localities']
            code, year = str(row['ID']['id']), str(row['ID']['year'])
            hebrew, english = row['name_heb'], row.get('name_eng')
            if not code.isdigit() or not year.isdigit() or not isinstance(hebrew, str) or not hebrew.strip():
                raise ValueError('Invalid CBS identity/name')
            if english is not None and not isinstance(english, str):
                raise ValueError('Invalid CBS English name')
            records.append({'id': code, 'year': year, 'name_heb': hebrew.strip(), 'name_eng': english.strip() if english else None, 'locality_type': row.get('locality_type')})
        except (KeyError, TypeError) as error:
            raise ValueError('Unexpected CBS locality record') from error
    return records


def fetch_snapshot(year=None, fetch_page=request_page, minimum_records=500):
    records, seen = [], set()
    for page in range(1, 101):
        batch = parse_page(fetch_page(page, year))
        for row in batch:
            key = (row['id'], row['year'])
            if key in seen:
                raise ValueError('Duplicate locality/year or repeated page; snapshot rejected')
            seen.add(key)
            records.append(row)
        if not batch:
            break
    else:
        raise ValueError('CBS pagination did not terminate')
    if len(records) < minimum_records:
        raise ValueError('Suspiciously small/empty CBS snapshot; previous snapshot retained')
    years = {row['year'] for row in records}
    if len(years) != 1 or (year is not None and years != {str(year)}):
        raise ValueError('Mixed or unexpected CBS data vintage')
    return {'schema_version': 1, 'source': URL, 'retrieved_at': datetime.now(timezone.utc).isoformat(), 'data_year': next(iter(years)), 'records': sorted(records, key=lambda row: int(row['id']))}


def refresh(path, year=None, fetch_page=request_page, minimum_records=500):
    path = Path(path)
    previous = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'records': []}
    snapshot = fetch_snapshot(year, fetch_page, minimum_records)
    old = {row['id']: row for row in previous['records']}
    new = {row['id']: row for row in snapshot['records']}
    report = ['# CBS snapshot changes', '', 'Candidates only: missing records are NOT automatically obsolete.', '', f'Data year: {snapshot["data_year"]}', '']
    for code in sorted(old.keys() | new.keys(), key=int):
        if code not in old:
            report.append(f'- NEW CANDIDATE {code}: {new[code]["name_heb"]} / {new[code]["name_eng"]}')
        elif code not in new:
            report.append(f'- MISSING FROM SOURCE, REVIEW {code}: {old[code]["name_heb"]}')
        elif old[code] != new[code]:
            report.append(f'- CHANGED, REVIEW {code}: {old[code]} -> {new[code]}')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)
    path.with_name('cbs_changes.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    return snapshot


def translations_from_snapshot(path):
    if not Path(path).exists():
        return {}
    snapshot = json.loads(Path(path).read_text(encoding='utf-8'))
    rows = snapshot['records']
    counts = Counter(row['name_heb'] for row in rows)
    return {row['name_heb']: row['name_eng'] for row in rows if counts[row['name_heb']] == 1 and row.get('name_eng')}
