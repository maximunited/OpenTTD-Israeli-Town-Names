"""Build all three GRFs and their BaNaNaS upload bundles into dist/."""
from pathlib import Path
import argparse
import re
import shutil
import subprocess
import sys
import zipfile

from make_english import BASE, read_release_version

REPO_URL = 'https://github.com/maximunited/OpenTTD-Israeli-Town-Names'
VARIANTS = {
    'hebrew': {
        'nml': 'israel.nml',
        'lang': 'lang',
        'title': 'Israeli town names',
        'styles': 'Israeli',
    },
    'english': {
        'nml': 'israel_english.nml',
        'lang': 'lang_english',
        'title': 'Israeli Town Names (English)',
        'styles': 'Israeli (English)',
    },
    'bilingual': {
        'nml': 'israel_bilingual.nml',
        'lang': 'lang_bilingual',
        'title': 'Israeli Town Names (Hebrew + English)',
        'styles': 'Israeli (Hebrew) and Israeli (English)',
    },
}


def find_nmlc():
    beside_python = Path(sys.executable).parent / ('nmlc.exe' if sys.platform == 'win32' else 'nmlc')
    found = beside_python if beside_python.exists() else shutil.which('nmlc')
    if not found:
        raise SystemExit('nmlc not found. Install it with: python -m pip install -r requirements-build.txt')
    return str(found)


def changelog_section(changelog, release):
    match = re.search(rf'^## {re.escape(release)}\s*$(.*?)(?=^## |\Z)', changelog, re.M | re.S)
    if not match or not match[1].strip():
        raise ValueError(f'CHANGELOG.md has no "## {release}" section')
    return match[1].strip()


def package(variant, grf, release, dist, base=BASE):
    info = VARIANTS[variant]
    folder = dist / f'israeli_town_names_{variant}-{release}'
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    shutil.copyfile(grf, folder / f'israeli_town_names_{variant}.grf')
    readme = (base / 'packaging' / 'readme.txt').read_text(encoding='utf-8')
    (folder / 'readme.txt').write_text(
        readme.format(title=info['title'], version=release, styles=info['styles'], url=REPO_URL),
        encoding='utf-8',
    )
    shutil.copyfile(base / 'CHANGELOG.md', folder / 'changelog.txt')
    shutil.copyfile(base / 'LICENSE', folder / 'license.txt')
    archive = dist / f'{folder.name}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as handle:
        for path in sorted(folder.iterdir()):
            handle.write(path, f'{folder.name}/{path.name}')
    return folder, archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--print-version', action='store_true', help='print the release version and exit')
    args = parser.parse_args()
    release = read_release_version(BASE / 'custom_tags.txt')
    if args.print_version:
        print(release)
        return
    notes = changelog_section((BASE / 'CHANGELOG.md').read_text(encoding='utf-8'), release)
    subprocess.run([sys.executable, 'make_english.py'], cwd=BASE, check=True)
    nmlc = find_nmlc()
    dist = BASE / 'dist'
    dist.mkdir(exist_ok=True)
    for variant, info in VARIANTS.items():
        grf = dist / f'israeli_town_names_{variant}.grf'
        subprocess.run([nmlc, '-c', '--lang-dir', info['lang'], '--grf', str(grf), info['nml']], cwd=BASE, check=True)
        folder, archive = package(variant, grf, release, dist)
        grf.unlink()
        print(f'Built {archive.relative_to(BASE)}')
    (dist / 'release-notes.md').write_text(
        f'{notes}\n\nUpload guide: {REPO_URL}/blob/master/docs/PUBLISHING.md\n', encoding='utf-8'
    )


if __name__ == '__main__':
    main()
