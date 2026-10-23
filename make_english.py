"""Build English town names using explicit overrides and an existing cache.
No automatic transliteration or network lookup. Unresolved names stop the build.
Review town_names_review.csv: cached labels are candidates, not verified names.
"""
from pathlib import Path
import argparse
import csv
import json
import re

BASE = Path(__file__).resolve().parent

NAME_OVERRIDES = {
    "יתיר": "Yatir",
    "נגוהות": "Negohot",
    "ברוכין": "Brukhin",
    "אל-עזי": "Al-Azi",
    "כחלה": "Kuhla",
    "חברון": "Hebron",
    "קציר": "Katzir",
    "עלי זהב": "Alei Zahav",
    "אלפי מנשה": "Alfei Menashe",
    "אלוני הבשן": "Alonei HaBashan",
    "אלמוג": "Almog",
    "עלמון": "Almon",
    "אניעם": "Aniam",
    "ארגמן": "Argaman",
    "אשדות יעקב (איחוד)": "Ashdot Ya'akov (Ihud)",
    "אשדות יעקב (מאוחד)": "Ashdot Ya'akov (Meuhad)",
    "עטרת": "Ateret",
    "אבנת": "Avnat",
    "אבני איתן": "Avnei Eitan",
    "בת חצור": "Bat Hatzor",
    "בית ג'ן": "Beit Jann",
    "בני יהודה": "Bnei Yehuda",
    "בקעות": "Beka'ot",
    "ברכה": "Brakha",
    "בית הערבה": "Beit HaArava",
    "בית חנן": "Beit Hanan",
    "בית חירות": "Beit Herut",
    "בית חורון": "Beit Horon",
    "בית רבן": "Beit Rabban",
    "בית זיד": "Beit Zaid",
    "ביתר עילית": "Beitar Illit",
    "דבוריה": "Dabburiyya",
    "דגניה א'": "Degania Alef",
    "דגניה ב'": "Degania Bet",
    "דבירה": "Dvira",
    "אפרת": "Efrat",
    "אל-רום": "El-Rom",
    "אלון מורה": "Elon Moreh",
    "אלקנה": "Elkana",
    "עין איילה": "Ein Ayala",
    "עין חרוד (איחוד)": "Ein Harod (Ihud)",
    "עין חרוד (מאוחד)": "Ein Harod (Meuhad)",
    "עין זיוון": "Ein Zivan",
    "ענב": "Enav",
    "אשכולות": "Eshkolot",
    "איתנים": "Eitanim",
    "אתגר": "Atgar",
    "גלעד (אבן יצחק)": "Galed (Even Yitzhak)",
    "עץ אפרים": "Etz Efraim",
    "גן שלמה": "Gan Shlomo",
    "גת (קיבוץ)": "Gat (Kibbutz)",
    "גשור": "Geshur",
    "גיבתון": "Gibton",
    "גלגל": "Gilgal",
    "גינתון": "Ginnaton",
    "גיניגר": "Ginegar",
    "גיתית": "Gitit",
    "גבעת חיים (איחוד)": "Givat Haim (Ihud)",
    "גבעת חיים (מאוחד)": "Givat Haim (Meuhad)",
    "גבעת יואב": "Givat Yoav",
    "גבעון החדשה": "Giv'on HaHadasha",
    "חד-נס": "Had Nes",
    "חגי": "Hagai",
    "נוה צוף": "Neve Tzuf",
    "חלוץ": "Halutz",
    "חמרה": "Hamra",
    "הר אדר": "Har Adar",
    "הר גילה": "Har Gilo",
    "חספין": "Hispin",
    "הוואשלה (שבט)": "Hawashla (Tribe)",
    "חצר בארותיים": "Hatzer Be'erotayim",
    "חצרות חולדה": "Hatzerot Hulda",
    "חפצי-בה": "Heftziba",
    "חמד": "Hemed",
    "חבר": "Hever",
    "הילה": "Hila",
    "חיננית": "Hinanit",
    "איתמר": "Itamar",
    "כדורי": "Kadoorie",
    "כרי דשא": "Karei Deshe",
    "כרמי צור": "Karmei Tzur",
    "כרמיאל": "Karmiel",
    "כפר בן נון": "Kfar Bin Nun",
    "כפר עציון": "Kfar Etzion",
    "כפר האורנים": "Kfar HaOranim",
    "כפר חרוב": "Kfar Haruv",
    "כפר ראש הנקרה": "Kfar Rosh HaNikra",
    "כפר תפוח": "Kfar Tapuach",
    "כנרת (מושבה)": "Kinneret (Moshava)",
    "כנרת (קבוצה)": "Kinneret (Kvutza)",
    "כוכב השחר": "Kokhav HaShahar",
    "כוכב יאיר": "Kokhav Yair",
    "כסיפה": "Kuseife",
    "שריגים (לי-און)": "Srigim (Li-On)",
    "לבנים": "Livnim",
    "לוחמי הגיטאות": "Lohamei HaGeta'ot",
    "מעלה אדומים": "Ma'ale Adumim",
    "מעלה עמוס": "Ma'ale Amos",
    "מעלה אפרים": "Ma'ale Efraim",
    "מעלה גמלא": "Ma'ale Gamla",
    "מעלה לבונה": "Ma'ale Levona",
    "מעלה מכמש": "Ma'ale Mikhmas",
    "מעש": "Ma'as",
    "מעין ברוך": "Ma'ayan Baruch",
    "מעין צבי": "Ma'ayan Tzvi",
    "מרגליות": "Margaliot",
    "משכיות": "Maskiot",
    "מתתיהו": "Matityahu",
    "מרום גולן": "Merom Golan",
    "מבוא דותן": "Mevo Dotan",
    "מבוא חמה": "Mevo Hama",
    "מצדות יהודה": "Metzadot Yehuda",
    "מיצר": "Meitzar",
    "מגדלים": "Migdalim",
    "מקווה ישראל": "Mikveh Israel",
    "מצפה שלם": "Mitzpe Shalem",
    "מצפה יריחו": "Mitzpe Yericho",
    "מודיעין עילית": "Modi'in Illit",
    "מודיעין-מכבים-רעות": "Modi'in-Maccabim-Re'ut",
    "חמדת": "Hemdat",
    "נחליאל": "Nahliel",
    "נטור": "Natur",
    "נאות גולן": "Neot Golan",
    "נעורים": "Neurim",
    "נתיב הגדוד": "Netiv HaGdud",
    "נווה אבות": "Neve Avot",
    "נווה דניאל": "Neve Daniel",
    "נופים": "Nofim",
    "נוקדים": "Nokdim",
    "אודם": "Odem",
    "עופרה": "Ofra",
    "אומן": "Omen",
    "אורנים": "Oranim",
    "אורנית": "Oranit",
    "עתניאל": "Otniel",
    "פדואל": "Peduel",
    "פני חבר": "Pnei Hever",
    "פקיעין חדשה": "Peki'in HaHadasha",
    "פסגות": "Psagot",
    "פצאל": "Petzael",
    "קרני שומרון": "Karnei Shomron",
    "קצרין": "Katzrin",
    "קדומים": "Kedumim",
    "קלע": "Kela",
    "קדמת צבי": "Kidmat Tzvi",
    "קרית ענבים": "Kiryat Anavim",
    "קרית ארבע": "Kiryat Arba",
    "קרית אתא": "Kiryat Ata",
    "קרית ביאליק": "Kiryat Bialik",
    "קרית עקרון": "Kiryat Ekron",
    "קרית גת": "Kiryat Gat",
    "קרית מלאכי": "Kiryat Malakhi",
    "קרית מוצקין": "Kiryat Motzkin",
    "קרית נטפים": "Kiryat Netafim",
    "קרית אונו": "Kiryat Ono",
    "קרית שלמה": "Kiryat Shlomo",
    "קרית שמונה": "Kiryat Shmona",
    "קרית טבעון": "Kiryat Tivon",
    "קרית ים": "Kiryat Yam",
    "קרית יערים": "Kiryat Yearim",
    "רם-און": "Ram-On",
    "ריחן": "Reihan",
    "רבבה": "Revava",
    "רועי": "Ro'i",
    "ראש צורים": "Rosh Tzurim",
    "רותם": "Rotem",
    "סלעית": "Sal'it",
    "שער מנשה": "Sha'ar Menashe",
    "שערי תקווה": "Sha'arei Tikva",
    "שדמות מחולה": "Shadmot Mehola",
    "שני": "Shani",
    "שקד": "Shaked",
    "שבי שומרון": "Shavei Shomron",
    "שילה": "Shilo",
    "שמעה": "Shim'a",
    "סוסיה": "Susya",
    "תאשור": "Te'ashur",
    "תל אביב - יפו": "Tel Aviv-Yafo",
    "תל שבע": "Tel Sheva",
    "תלם": "Telem",
    "טנא": "Tene",
    "תקוע": "Tekoa",
    "ורד יריחו": "Vered Yericho",
    "יעל": "Yael",
    "יקיר": "Yakir",
    "יקנעם (מושבה)": "Yokneam (Moshava)",
    "צופים": "Tzufim",
    "צביה": "Tzvia",
    "סנסנה": "Sansana",
    "אירוס": "Irus",
    "נמרוד": "Nimrod",
    "רחלים": "Rehelim",
    "מבואות יריחו": "Mevo'ot Yericho",
    "אפיקים": "Afikim",
    "לוטם": "Lotem",
    "אשקלון": "Ashkelon",
    "לכיש": "Lachish",
    "סגולה": "Segula",
    "פטיש": "Patish",
    "פדויים": "Peduyim",
    "מלאה": "Mele'a",
    "שבי דרום": "Shavei Darom",
    "כנות": "Kanot",
    "כפר החורש": "Kfar HaHoresh",
    "כפר קיש": "Kfar Kish",
    "כנף": "Kanaf",
    "מעגלים": "Ma'agalim",
    "חירות": "Herut",
    "בית אל": "Beit El",
    "בית לחם הגלילית": "Beit Lehem HaGlilit",
    "עין דור": "Ein Dor",
    "יצהר": "Yitzhar",
    "מזרע": "Mizra",
    "בטחה": "Bitha",
    "בסמ\"ה": "Basma",
    "בני עי\"ש": "Bnei Ayish",
    "דוב\"ב": "Dovev",
    "עין הנצי\"ב": "Ein HaNatziv",
    "גבעת ח\"ן": "Givat Hen",
    "גבעת כ\"ח": "Givat Koah",
    "גבעת ניל\"י": "Givat Nili",
    "חצרות כ\"ח": "Hatzerot Koah",
    "כפר ביל\"ו": "Kfar Bilu",
    "כפר חב\"ד": "Kfar Chabad",
    "כפר הרי\"ף": "Kfar HaRif",
    "כפר הרא\"ה": "Kfar HaRoeh",
    "כפר מל\"ל": "Kfar Malal",
    "כרם מהר\"ל": "Kerem Maharal",
    "מצפה אבי\"ב": "Mitzpe Aviv",
    "נתיב הל\"ה": "Netiv HaLamed-Heh",
    "נווה אטי\"ב": "Neve Ativ",
    "ניל\"י": "Nili",
    "ניר ח\"ן": "Nir Hen",
    "פעמי תש\"ז": "Pa'amei Tashaz",
    "תלמי ביל\"ו": "Talmei Bilu",
    "יד רמב\"ם": "Yad Rambam",
    "ייט\"ב": "Yitav"
}

TEXT_PATTERN = re.compile(r'text\("((?:\\.|[^"\\])*)",\s*(\d+)\s*\)')
TOKEN_PATTERN = re.compile(r'"(?:\\.|[^"\\])*"|/\*[\s\S]*?\*/|//[^\n]*')
HEBREW = re.compile(r'[\u0590-\u05ff]')

def without_comments(source):
    def replace(match):
        value = match.group()
        if value.startswith('"'):
            return value
        return '\n' * value.count('\n')
    return TOKEN_PATTERN.sub(replace, source)

def decode(value):
    return re.sub(r'\\(["\\])', r'\1', value)

def encode(value):
    return value.replace('\\', '\\\\').replace('"', '\\"')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--amnon', action='store_true',
                        help='Prefer Amnon over Amnun for אמנון (spelling preference).')
    args = parser.parse_args()
    overrides = dict(NAME_OVERRIDES)
    if args.amnon:
        overrides['אמנון'] = 'Amnon'
    source = without_comments((BASE / 'israel.nml').read_text(encoding='utf-8-sig'))
    cache_path = BASE / 'english_names_cache.json'
    cache = json.loads(cache_path.read_text(encoding='utf-8-sig')) if cache_path.exists() else {}
    extra_path = BASE / 'english_name_overrides.json'
    if extra_path.exists():
        overrides.update(json.loads(extra_path.read_text(encoding='utf-8-sig')))
    names = list(dict.fromkeys(decode(m.group(1)) for m in TEXT_PATTERN.finditer(source)))
    resolved = {}
    rows = []
    missing = []
    for name in names:
        value = overrides.get(name) or cache.get(name)
        origin = 'manual override' if name in overrides else 'cached label: review'
        if not isinstance(value, str) or not value.strip() or HEBREW.search(value):
            value = ''
            origin = 'UNRESOLVED'
            missing.append(name)
        resolved[name] = value
        rows.append({'hebrew': name, 'english': value, 'source': origin})
    with (BASE / 'town_names_review.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['hebrew', 'english', 'source'])
        writer.writeheader()
        writer.writerows(rows)
    (BASE / 'unmatched_hebrew_names.txt').write_text('\n'.join(missing), encoding='utf-8-sig')
    if missing:
        raise SystemExit(f'{len(missing)} unresolved names. See unmatched_hebrew_names.txt. '
                         'Add exact Hebrew-to-English entries to english_name_overrides.json, then rerun. '
                         'Existing NML output was NOT updated; do not compile stale output.')
    def replace(match):
        return f'text("{encode(resolved[decode(match.group(1))])}", {match.group(2)})'
    output = TEXT_PATTERN.sub(replace, source)
    original_id = r'grfid: "ZH\01\01";'
    if original_id not in output:
        raise SystemExit('Original GRFID not found. Inspect israel.nml before changing IDs.')
    output = output.replace(original_id, r'grfid: "ZH\01\02";', 1)
    output = re.sub(r'\breal\b', 'real_english', output)
    if any(HEBREW.search(decode(m.group(1))) for m in TEXT_PATTERN.finditer(output)):
        raise SystemExit('Validation failed: Hebrew remains in town-name entries.')
    (BASE / 'israel_english.nml').write_text(output, encoding='utf-8')
    language_dir = BASE / 'lang_english'
    language_dir.mkdir(exist_ok=True)
    (language_dir / 'english.lng').write_text(
        '##grflangid 0x01\n\n'
        'STR_GRF_NAME :Israeli Town Names (English) {VERSION}\n'
        'STR_GRF_DESCRIPTION :Israeli town names in English\n'
        'STR_STYLES :Israeli (English)\n', encoding='utf-8')
    print(f'Active unique names: {len(names)}')
    print(f'Manual overrides used: {sum(n in overrides for n in names)}')
    print(f'Cached labels used (not independently verified): {sum(n not in overrides for n in names)}')
    print('Unresolved: 0; Hebrew town-name strings: 0')
    print('Wrote israel_english.nml, lang_english/english.lng, town_names_review.csv')

if __name__ == '__main__':
    main()
