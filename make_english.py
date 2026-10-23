"""Generate English NML from committed translations; never guess missing names."""
from pathlib import Path
import argparse
import csv
import json
import re

BASE = Path(__file__).resolve().parent
TEXT = re.compile(r'text\("((?:\\.|[^"\\])*)",\s*(\d+)\s*\)')
TOKENS = re.compile(r'"(?:\\.|[^"\\])*"|/\*[\s\S]*?\*/|//[^\n]*')
HEBREW = re.compile(r'[\u0590-\u05ff]')


def strip_comments(source):
    return TOKENS.sub(lambda m: m[0] if m[0].startswith('"') else '\n' * m[0].count('\n'), source)


def decode(value):
    return re.sub(r'\\(["\\])', r'\1', value)


def encode(value):
    return value.replace('\\', '\\\\').replace('"', '\\"')


def read_mapping(path):
    if not path.exists():
        return {}
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'{path}: duplicate key {key!r}')
            result[key] = value
        return result
    result = json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_pairs)
    if not isinstance(result, dict):
        raise ValueError(f'{path}: expected a JSON object')
    for key, value in result.items():
        if not isinstance(value, str) or not value.strip() or HEBREW.search(value) or any(ord(c) < 32 for c in value):
            raise ValueError(f'{path}: invalid English translation for {key!r}')
    return result


def resolve_translations(cache, overrides, amnon=False):
    translations = cache | overrides
    if amnon:
        translations['אמנון'] = 'Amnon'
    return translations


def generate(source, translations):
    source = strip_comments(source)
    names = list(dict.fromkeys(decode(m[1]) for m in TEXT.finditer(source)))
    if not names:
        raise ValueError('No town names found')
    missing = [name for name in names if name not in translations]
    if missing:
        raise ValueError(f'{len(missing)} unresolved names; see town_names_review.csv')
    original = r'grfid: "ZH\01\01";'
    if source.count(original) != 1:
        raise ValueError('Expected original GRFID exactly once; inspect source before continuing')
    output = TEXT.sub(lambda m: f'text("{encode(translations[decode(m[1])])}", {m[2]})', source)
    output = output.replace(original, r'grfid: "ZH\01\02";', 1)
    output = re.sub(r'town_names\(real(?=\s*[,\)])', 'town_names(real_english', output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--overrides', type=Path, default=BASE / 'english_name_overrides.json')
    parser.add_argument('--amnon', action='store_true', help='Prefer Amnon to the cached spelling for אמנון')
    args = parser.parse_args()
    cache = read_mapping(BASE / 'english_names_cache.json')
    overrides = read_mapping(args.overrides)
    translations = resolve_translations(cache, overrides, args.amnon)
    source = (BASE / 'israel.nml').read_text(encoding='utf-8-sig')
    names = list(dict.fromkeys(decode(m[1]) for m in TEXT.finditer(strip_comments(source))))
    with (BASE / 'town_names_review.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['hebrew', 'english', 'source'])
        for name in names:
            origin = 'CLI spelling preference' if args.amnon and name == 'אמנון' else 'manual override' if name in overrides else 'cached label: UNVERIFIED' if name in cache else 'UNRESOLVED'
            writer.writerow([name, translations.get(name, ''), origin])
    destination = BASE / 'israel_english.nml'
    try:
        output = generate(source, translations)
    except ValueError as error:
        raise SystemExit(f'{error}. Output NOT updated; do not compile a stale NML file.') from error
    destination.write_text(output, encoding='utf-8')
    print(f'Wrote {destination.name}: {len(names)} unique active names. Review cached labels before release.')


if __name__ == '__main__':
    main()
