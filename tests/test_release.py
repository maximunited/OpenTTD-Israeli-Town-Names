import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from build import VARIANTS, changelog_section, package
from make_english import (
    BASE, TEXT, check_versions, decode, generate, generate_bilingual, grf_version_number,
    grf_versions, read_mapping, read_release_version, source_names, strip_comments,
)
from review_rules import is_non_town

SOURCE = r'grfid: "ZH\01\01";' + '\nversion: 200;\nmin_compatible_version: 200;\ntown_names(real) { { text("עיר", 1), text("כפר \\"א\\"", 2) } }'


def committed_source():
    return (BASE / 'israel.nml').read_text(encoding='utf-8-sig')


class VersionTests(unittest.TestCase):
    def test_version_number(self):
        self.assertEqual(grf_version_number('0.2.0'), 200)
        self.assertEqual(grf_version_number('1.10.3'), 11003)
        with self.assertRaises(ValueError):
            grf_version_number('0.100.0')

    def test_committed_versions_consistent(self):
        release = read_release_version(BASE / 'custom_tags.txt')
        check_versions(committed_source(), release)

    def test_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, 'version: 300'):
            check_versions(SOURCE, '0.3.0')

    def test_release_version_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'custom_tags.txt'
            path.write_text('VERSION  :v2\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                read_release_version(path)

    def test_changelog_has_current_release(self):
        release = read_release_version(BASE / 'custom_tags.txt')
        self.assertTrue(changelog_section((BASE / 'CHANGELOG.md').read_text(encoding='utf-8'), release))

    def test_changelog_section_extracted(self):
        text = '# Changelog\n\n## 0.2.0\n\n- new\n\n## 0.1.1\n\n- old\n'
        self.assertEqual(changelog_section(text, '0.2.0'), '- new')
        with self.assertRaises(ValueError):
            changelog_section(text, '0.3.0')


class BilingualTests(unittest.TestCase):
    def test_bilingual_has_both_styles(self):
        output = generate_bilingual(SOURCE, {'עיר': 'Town', 'כפר "א"': 'Kfar "A"'})
        self.assertIn(r'grfid: "MA\01\02";', output)
        self.assertEqual(grf_versions(output), (200, 200))
        self.assertIn('text("עיר", 1)', output)
        self.assertIn('text("Kfar \\"A\\"", 2)', output)
        self.assertIn('styles: string(STR_STYLE_HEBREW);', output)
        self.assertIn('town_names(real_english, 1)', output)

    def test_bilingual_rejects_missing_translation(self):
        with self.assertRaises(ValueError):
            generate_bilingual(SOURCE, {'עיר': 'Town'})

    def test_grf_ids_distinct(self):
        translations = {'עיר': 'Town', 'כפר "א"': 'Kfar'}
        ids = {re.search(r'grfid: "([^"]+)"', text)[1] for text in (SOURCE, generate(SOURCE, translations), generate_bilingual(SOURCE, translations))}
        self.assertEqual(len(ids), 3)

    def test_committed_bilingual_keeps_every_name(self):
        source = committed_source()
        translations = read_mapping(BASE / 'english_names_cache.json') | read_mapping(BASE / 'english_name_overrides.json') | read_mapping(BASE / 'display_name_preferences.json')
        output = generate_bilingual(source, translations)
        self.assertEqual(len(TEXT.findall(output)), 2 * len(TEXT.findall(source.split('/*')[0])))


class PlayableListTests(unittest.TestCase):
    def test_no_non_towns_in_playable_list(self):
        # מחנה יתיר is a real community (CBS type 350) despite the "camp" prefix.
        allowed = {'מחנה יתיר'}
        flagged = [name for name in source_names(committed_source()) if is_non_town({'name_heb': name}) and name not in allowed]
        self.assertEqual(flagged, [])


class PackageTests(unittest.TestCase):
    def test_variant_lang_files_have_metadata(self):
        for variant, info in VARIANTS.items():
            text = (BASE / info['lang'] / 'english.lng').read_text(encoding='utf-8')
            for key in ('STR_GRF_NAME', 'STR_GRF_DESCRIPTION', 'STR_GRF_URL'):
                self.assertRegex(text, rf'(?m)^{key}\s*:\S', f'{variant}: {key}')
            self.assertRegex(text, r'(?m)^STR_GRF_URL\s*:https://github\.com/', variant)

    def test_bilingual_embeds_url(self):
        self.assertIn('url: string(STR_GRF_URL);', generate_bilingual(SOURCE, {'עיר': 'Town', 'כפר "א"': 'Kfar'}))

    def test_committed_source_embeds_url(self):
        self.assertIn('url: string(STR_GRF_URL);', strip_comments(committed_source()))

    def test_package_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp)
            grf = dist / 'fake.grf'
            grf.write_bytes(b'GRF')
            folder, archive = package('bilingual', grf, '0.2.0', dist)
            self.assertEqual(archive.name, 'israeli_town_names_bilingual-0.2.0.zip')
            names = sorted(path.name for path in folder.iterdir())
            # BaNaNaS refuses a license.txt when a standard license such as GPL v2 is selected.
            self.assertEqual(names, ['changelog.txt', 'israeli_town_names_bilingual.grf', 'readme.txt'])
            readme = (folder / 'readme.txt').read_text(encoding='utf-8')
            self.assertIn('Israeli Town Names (Hebrew + English) 0.2.0', readme)
            self.assertNotIn('{', readme)
            with zipfile.ZipFile(archive) as handle:
                self.assertEqual(sorted(handle.namelist()), [f'{folder.name}/{name}' for name in names])

    def test_license_is_gpl2(self):
        self.assertIn('GNU GENERAL PUBLIC LICENSE\n                       Version 2', (BASE / 'LICENSE').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
