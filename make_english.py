"""Generate English NML offline, or explicitly refresh CBS candidate data first."""
from pathlib import Path
import argparse
import csv
import json
import re
from cbs_directory import refresh, translations_from_snapshot
from review_rules import classify_candidate, normalize_english_label, resolve_mapping

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


def resolve_translations(cache, overrides):
    return cache | overrides


def generate(source, translations):
    source = strip_comments(source)
    names = list(dict.fromkeys(decode(m[1]) for m in TEXT.finditer(source)))
    if not names:
        raise ValueError('No town names found')
    missing = [name for name in names if name not in translations]
    if missing:
        raise ValueError(f'{len(missing)} unresolved names; see town_names_review.csv')
    for name in names:
        value = translations[name]
        if not isinstance(value, str) or not value.strip() or HEBREW.search(value) or any(ord(c) < 32 for c in value):
            raise ValueError(f'Invalid English name for {name!r}')
    original = r'grfid: "ZH\01\01";'
    if source.count(original) != 1:
        raise ValueError('Expected original GRFID exactly once')
    output = TEXT.sub(lambda m: f'text("{encode(translations[decode(m[1])])}", {m[2]})', source)
    output = output.replace(original, r'grfid: "ZH\01\02";', 1)
    return re.sub(r'town_names\(real(?=\s*[,\)])', 'town_names(real_english', output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--overrides', type=Path, default=BASE / 'english_name_overrides.json')
    parser.add_argument('--preferences', type=Path, default=BASE / 'display_name_preferences.json')
    parser.add_argument('--refresh-cbs', action='store_true')
    parser.add_argument('--cbs-year', type=int)
    args = parser.parse_args()
    if args.cbs_year and not args.refresh_cbs:
        parser.error('--cbs-year requires --refresh-cbs')
    snapshot_path = BASE / 'data' / 'cbs_localities.json'
    if args.refresh_cbs:
        refresh(snapshot_path, args.cbs_year)
    cbs = {hebrew: normalize_english_label(english) for hebrew, english in translations_from_snapshot(snapshot_path).items()}
    cache = read_mapping(BASE / 'english_names_cache.json')
    overrides = read_mapping(args.overrides)
    preferences = read_mapping(args.preferences)
    exclusions_path = BASE / 'data' / 'cbs_exclusions.json'
    exclusions = (
        json.loads(exclusions_path.read_text(encoding='utf-8-sig'))
        if exclusions_path.exists()
        else {}
    )
    translations = resolve_mapping(cbs, cache, overrides, preferences)
    source = (BASE / 'israel.nml').read_text(encoding='utf-8-sig')
    names = list(dict.fromkeys(decode(m[1]) for m in TEXT.finditer(strip_comments(source))))
    with (BASE / 'town_names_review.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['hebrew', 'english', 'source'])
        for name in sorted(names, key=lambda n: (translations.get(n, '').casefold(), n)):
            origin = 'display preference' if name in preferences else 'manual override' if name in overrides else 'cached label: UNVERIFIED' if name in cache else 'CBS exact-name candidate: REVIEW' if name in cbs else 'UNRESOLVED'
            writer.writerow([name, translations.get(name, ''), origin])
    if snapshot_path.exists():
        records = json.loads(snapshot_path.read_text(encoding='utf-8'))['records']
        existing = set(names)
        with (BASE / 'data' / 'cbs_candidates.csv').open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['id', 'year', 'hebrew', 'english', 'status'])
            for row in records:
                if row['name_heb'] not in existing:
                    english = normalize_english_label(row['name_eng']) if row['name_eng'] is not None else ''
                    exclusion = exclusions.get(str(row['id']))
                    if exclusion:
                        status = f"EXCLUDED: {exclusion['reason']}"
                    else:
                        status = classify_candidate(row, existing)
                    writer.writerow([row['id'], row['year'], row['name_heb'], english, status])
    output = generate(source, translations)
    (BASE / 'israel_english.nml').write_text(output, encoding='utf-8')
    print(f'Wrote English NML for {len(names)} unique active names; alphabetical review CSV written. Generation order preserved.')


if __name__ == '__main__':
    main()
