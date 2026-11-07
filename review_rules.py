"""Review rules for CBS candidates and English mapping precedence."""
import re

HEBREW = re.compile(r'[\u0590-\u05ff]')
CONTROL = re.compile(r'[\x00-\x1f\x7f]')

NON_TOWN_MARKERS = (
    '(שבט)',
    'תעשיון',
    'אזור תעשייה',
    'אזור תעסוקה',
    'מפעלי',
    'בית חולים',
    'מרכז אזורי',
    'מכללה',
    'בי"ס',
    'מ"א ',
    'של"ש',
    'קרית תעופה',
    'נמל תעופה',
    'נפת ',
    'מחנה ',
    'פארק תעשיות',
    'תעשיות ',
    'קרית חינוך',
    'ים המלח',
    'גמ"ל',
    'מחוז',
)

# CBS locality types: 460 Bedouin tribes, 520 industrial zones and regional centres,
# 530 statistical areas. Type 510 mixes real villages with camps and institutions,
# so it is left to the name markers above.
NON_TOWN_TYPES = frozenset({'460', '520', '530'})


def normalize_english_label(value):
    if not isinstance(value, str):
        raise ValueError('English label must be text')
    value = re.sub(r'\s+', ' ', value.strip().strip("'")).strip()
    return re.sub(r'(?<=\S)\(', ' (', value)


def validate_english_label(value, hebrew=None):
    value = normalize_english_label(value)
    if not value:
        raise ValueError(f'Empty English label for {hebrew!r}')
    if HEBREW.search(value):
        raise ValueError(f'Hebrew characters in English label for {hebrew!r}')
    if CONTROL.search(value):
        raise ValueError(f'Control characters in English label for {hebrew!r}')
    return value


def is_non_town(row):
    hebrew = row['name_heb']
    return (
        str(row.get('locality_type')) in NON_TOWN_TYPES
        or hebrew.endswith('*')
        or any(marker in hebrew for marker in NON_TOWN_MARKERS)
    )


def classify_candidate(row, playable_names):
    if row['name_heb'] in playable_names:
        return 'EXACT PLAYABLE MATCH'
    if is_non_town(row):
        return 'NOT A TOWN: REVIEW ELIGIBILITY'
    return 'NOT EXACTLY MATCHED: REVIEW ALIAS/ELIGIBILITY'


def resolve_mapping(cbs, cache, overrides, preferences):
    """Resolve English labels across CBS, cache, override, and preference layers.
    Precedence (highest wins): preference > override > cache > CBS.
    Each layer is applied only where a label is not already resolved.
    """
    layers = [
        ('preference', preferences),
        ('override', overrides),
        ('cache', cache),
        ('CBS', cbs),
    ]
    result = {}
    for layer, mapping in layers:
        if not isinstance(mapping, dict):
            raise ValueError(f'{layer} mapping must be a dictionary')
        for hebrew, english in mapping.items():
            if hebrew not in result:
                result[hebrew] = validate_english_label(english, hebrew)
    return result
