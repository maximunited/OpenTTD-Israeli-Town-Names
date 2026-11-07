"""Generate the English and bilingual NML offline, or explicitly refresh CBS candidate data first."""
from pathlib import Path
import argparse
import csv
import json
import logging
import re
from cbs_directory import refresh, translations_from_snapshot
from review_rules import is_non_town, normalize_english_label, resolve_mapping

BASE = Path(__file__).resolve().parent
TEXT = re.compile(r'text\("((?:\\.|[^"\\])*)",\s*(\d+)\s*\)')
TOKENS = re.compile(r'"(?:\\.|[^"\\])*"|/\*[\s\S]*?\*/|//[^\n]*')
HEBREW = re.compile(r'[\u0590-\u05ff]')
VERSION = re.compile(r'^\s*version:\s*(\d+)\s*;', re.M)
MIN_VERSION = re.compile(r'^\s*min_compatible_version:\s*(\d+)\s*;', re.M)
HEBREW_GRFID = r'grfid: "ZH\01\01";'
# "ZH" is the original author's prefix; this fork's own NewGRFs use "MA".
ENGLISH_GRFID = r'grfid: "MA\01\01";'
BILINGUAL_GRFID = r'grfid: "MA\01\02";'


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


def read_release_version(path):
    match = re.search(r'^VERSION\s*:\s*(\S+)\s*$', path.read_text(encoding='utf-8-sig'), re.M)
    if not match or not re.fullmatch(r'\d+\.\d+\.\d+', match[1]):
        raise ValueError(f'{path}: expected a line like "VERSION  :1.2.3"')
    return match[1]


def grf_version_number(release):
    major, minor, patch = (int(part) for part in release.split('.'))
    if minor > 99 or patch > 99:
        raise ValueError(f'Version {release}: minor and patch must be 0-99')
    return major * 10000 + minor * 100 + patch


def grf_versions(source):
    source = strip_comments(source)
    versions, minimums = VERSION.findall(source), MIN_VERSION.findall(source)
    if len(versions) != 1 or len(minimums) != 1:
        raise ValueError('Expected exactly one version and one min_compatible_version in the grf block')
    return int(versions[0]), int(minimums[0])


def check_versions(source, release):
    expected = grf_version_number(release)
    if grf_versions(source) != (expected, expected):
        raise ValueError(
            f'israel.nml must have "version: {expected};" and "min_compatible_version: {expected};" '
            f'for release {release} (see docs/PUBLISHING.md)'
        )


def source_names(source):
    return list(dict.fromkeys(decode(m[1]) for m in TEXT.finditer(strip_comments(source))))


def check_translations(names, translations):
    if not names:
        raise ValueError('No town names found')
    missing = [name for name in names if name not in translations]
    if missing:
        raise ValueError(f'{len(missing)} unresolved names; see town_names_review.csv')
    for name in names:
        value = translations[name]
        if not isinstance(value, str) or not value.strip() or HEBREW.search(value) or any(ord(c) < 32 for c in value):
            raise ValueError(f'Invalid English name for {name!r}')


def generate(source, translations):
    check_translations(source_names(source), translations)
    source = strip_comments(source)
    if source.count(HEBREW_GRFID) != 1:
        raise ValueError('Expected original GRFID exactly once')
    output = TEXT.sub(lambda m: f'text("{encode(translations[decode(m[1])])}", {m[2]})', source)
    output = output.replace(HEBREW_GRFID, ENGLISH_GRFID, 1)
    return re.sub(r'town_names\(real(?=\s*[,\)])', 'town_names(real_english', output)


def town_names_block(label, entries):
    body = ',\n'.join(f'\t\ttext("{encode(name)}", {weight})' for name, weight in entries)
    return f'town_names({label}) {{\n\t{{\n{body}\n\t}}\n}}\n'


def style_block(style, label):
    return f'town_names {{\n\tstyles: string({style});\n\t{{\n\t\ttown_names({label}, 1)\n\t}}\n}}\n'


def generate_bilingual(source, translations):
    check_translations(source_names(source), translations)
    version, minimum = grf_versions(source)
    entries = [(decode(m[1]), m[2]) for m in TEXT.finditer(strip_comments(source))]
    header = (
        f'grf {{\n\t{BILINGUAL_GRFID}\n\tname: string(STR_GRF_NAME);\n\tdesc: string(STR_GRF_DESCRIPTION);\n'
        f'\turl: string(STR_GRF_URL);\n'
        f'\tversion: {version};\n\tmin_compatible_version: {minimum};\n}}\n'
    )
    return '\n'.join([
        header,
        town_names_block('real_hebrew', entries),
        town_names_block('real_english', [(translations[name], weight) for name, weight in entries]),
        style_block('STR_STYLE_HEBREW', 'real_hebrew'),
        style_block('STR_STYLE_ENGLISH', 'real_english'),
    ])


def label_origin(name, layers):
    for label, mapping in layers:
        if name in mapping:
            return label
    return 'UNRESOLVED'


def write_review_csv(path, names, translations, layers):
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['hebrew', 'english', 'source'])
        for name in sorted(names, key=lambda n: (translations.get(n, '').casefold(), n)):
            writer.writerow([name, translations.get(name, ''), label_origin(name, layers)])


def write_candidates_csv(path, records, playable_names):
    """List CBS towns missing from the playable list; non-towns are left out entirely."""
    existing = set(playable_names)
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['id', 'year', 'locality_type', 'hebrew', 'english'])
        for row in records:
            if row['name_heb'] in existing or is_non_town(row):
                continue
            english = normalize_english_label(row['name_eng']) if row['name_eng'] is not None else ''
            writer.writerow([row['id'], row['year'], row.get('locality_type') or '', row['name_heb'], english])


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--overrides', type=Path, default=BASE / 'english_name_overrides.json')
    parser.add_argument('--preferences', type=Path, default=BASE / 'display_name_preferences.json')
    parser.add_argument('--refresh-cbs', action='store_true')
    parser.add_argument('--cbs-year', type=int)
    args = parser.parse_args()
    if args.cbs_year and not args.refresh_cbs:
        parser.error('--cbs-year requires --refresh-cbs')
    source = (BASE / 'israel.nml').read_text(encoding='utf-8-sig')
    check_versions(source, read_release_version(BASE / 'custom_tags.txt'))
    snapshot_path = BASE / 'data' / 'cbs_localities.json'
    if args.refresh_cbs:
        refresh(snapshot_path, args.cbs_year)
    cbs = {hebrew: normalize_english_label(english) for hebrew, english in translations_from_snapshot(snapshot_path).items()}
    cache = read_mapping(BASE / 'english_names_cache.json')
    overrides = read_mapping(args.overrides)
    preferences = read_mapping(args.preferences)
    translations = resolve_mapping(cbs, cache, overrides, preferences)
    names = source_names(source)
    layers = [
        ('display preference', preferences),
        ('manual override', overrides),
        ('cached label: UNVERIFIED', cache),
        ('CBS exact-name candidate: REVIEW', cbs),
    ]
    write_review_csv(BASE / 'town_names_review.csv', names, translations, layers)
    if snapshot_path.exists():
        records = json.loads(snapshot_path.read_text(encoding='utf-8'))['records']
        write_candidates_csv(BASE / 'data' / 'cbs_candidates.csv', records, names)
    (BASE / 'israel_english.nml').write_text(generate(source, translations), encoding='utf-8')
    (BASE / 'israel_bilingual.nml').write_text(generate_bilingual(source, translations), encoding='utf-8')
    print(f'Wrote English and bilingual NML for {len(names)} town names; review CSV written.')


if __name__ == '__main__':
    main()
