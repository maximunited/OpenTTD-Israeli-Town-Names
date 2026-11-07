# From repo to BaNaNaS

This guide takes a change from this repository to a published package that
OpenTTD players can download in-game. BaNaNaS is OpenTTD's content service
(the "Online Content" button in the game).

## The three NewGRFs

| Variant | File | GRF ID | Who can publish it on BaNaNaS |
|---|---|---|---|
| English | `israeli_town_names_english.grf` | `MA\01\01` | You (new package) |
| Hebrew + English | `israeli_town_names_bilingual.grf` | `MA\01\02` | You (new package) |
| Hebrew | `israeli_town_names_hebrew.grf` | `ZH\01\01` | Only ZvikaZ (the original author) |

- The **bilingual** GRF adds two entries to the in-game "Town names" list:
  "Israeli (Hebrew)" and "Israeli (English)". The player picks one per game.
- The **Hebrew** GRF is already on BaNaNaS as
  [Israeli town names 0.1.1](https://bananas.openttd.org/package/newgrf/5a480101),
  owned by ZvikaZ. BaNaNaS only accepts new versions of a package from its
  owner. To publish our Hebrew changes, open a pull request at
  https://github.com/ZvikaZ/OpenTTD-Israeli-Town-Names or send him the built file.
  Do not upload it under a new GRF ID: players would see two Hebrew sets.
- The GRF ID is how OpenTTD and BaNaNaS recognise a package. **Never change
  an ID after publishing.**

Recommended: publish the **bilingual** package. Publish the English one too
if you want an English-only choice.

## 1. Make the change

- Town name list: `israel.nml` (Hebrew, one `text("...", 1),` line per town).
- English spellings: see [NAME_DATA.md](NAME_DATA.md).
- Run the tests: `python -m unittest discover -s tests`

## 2. Set the version

The version lives in **three places**, and the tests fail if they disagree:

1. `custom_tags.txt`: `VERSION  :0.3.0`
2. `israel.nml`, in the `grf { }` block, both lines set to the same number:
   ```
   version: 300;
   min_compatible_version: 300;
   ```
   The number is `major × 10000 + minor × 100 + patch`. For example,
   0.2.0 → 200, 0.3.0 → 300, 1.0.0 → 10000, 1.2.3 → 10203.
3. `CHANGELOG.md`: add a `## 0.3.0` section listing the changes.

Why `min_compatible_version` equals `version`: OpenTTD stores which GRF a
savegame used and regenerates town names from it when the save loads.
If the name list changes, an old save loaded with the new GRF would see its
towns renamed. Raising `min_compatible_version` makes OpenTTD keep using the
old version for old saves (BaNaNaS keeps old versions for this).

Which part to bump:

| Change | Example |
|---|---|
| Spelling fixes, a few towns added or removed | 0.2.0 → 0.2.1 |
| Many towns, new variant, other noticeable change | 0.2.0 → 0.3.0 |

## 3. Build

**Easiest:** open a pull request. CI builds everything. On the run's
"Summary" page, under **Artifacts**, download `israeli-town-names-english`,
`-bilingual` or `-hebrew`.

**Locally** (Python 3.12+):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe build.py
```

On Linux/macOS use `.venv/bin/python`. The output goes to `dist/`:

```
dist/
  israeli_town_names_bilingual-0.2.0/   <- the files to upload
    israeli_town_names_bilingual.grf
    readme.txt       (shown in-game)
    changelog.txt    (shown in-game)
    license.txt      (shown in-game)
  israeli_town_names_bilingual-0.2.0.zip
  ...same for english and hebrew
  release-notes.md
```

## 4. Test in OpenTTD

Do this before every upload; it takes two minutes.

1. Close OpenTTD.
2. Copy a variant's **folder** from `dist/` into your OpenTTD `newgrf`
   folder. In Steam: right-click OpenTTD > Manage > Browse local files.
   Otherwise it is usually `Documents\OpenTTD\newgrf` on Windows or
   `~/.local/share/openttd/newgrf` on Linux.
3. Start OpenTTD, open **NewGRF Settings**, click **Rescan files** and
   activate the GRF. Check the name, version and readme in the panel.
4. Start a new game. In the "Town names" list choose the Israeli style.
   For the bilingual GRF, try both styles.
5. Check that names look right on the map. If Hebrew letters show as boxes,
   turn off **Use traditional sprite font** in Game Options > Graphics.
6. Remove the test copy afterwards, so it does not clash with the version
   you download from BaNaNaS.

## 5. Release on GitHub

After the pull request is merged into `master`:

```powershell
git switch master
git pull
git tag v0.2.0
git push origin v0.2.0
```

The tag must be `v` + the version in `custom_tags.txt`, or the release fails.
The **Release** workflow tests, builds and creates a GitHub release with the
three zips attached. Use those zips for the upload below.

## 6. Upload to BaNaNaS

1. Go to https://bananas.openttd.org/manager and choose **Login via GitHub**.
2. Start a new upload and add the **four files** from the variant's folder:
   the `.grf`, `readme.txt`, `changelog.txt` and `license.txt`.
3. BaNaNaS reads the GRF and recognises the package by its GRF ID.
   - First upload of a GRF ID: a new package is created.
   - Later uploads with the same GRF ID: a new version of your package.
4. Fill in the form using the defaults below, then publish.
5. Check the package page, then in-game: Online Content, search "Israeli".

The site's labels may differ slightly from these steps; the fields are the same.

### Defaults

| Field | English | Hebrew + English |
|---|---|---|
| Name | Israeli Town Names (English) | Israeli Town Names (Hebrew + English) |
| Version | same as `custom_tags.txt`, e.g. `0.2.0` | same |
| License | GPL v2 | GPL v2 |
| Description | Real Israeli town names in English, based on the original Hebrew set by ZvikaZ. | Real Israeli town names with two town name styles: Hebrew and English. Based on the original Hebrew set by ZvikaZ. |
| URL | https://github.com/maximunited/OpenTTD-Israeli-Town-Names | same |
| Tags | `town names`, `israel` | `town names`, `israel`, `hebrew` |
| Region | Israel (if offered) | Israel (if offered) |
| Compatibility | leave the default | leave the default |
| Dependencies | none | none |

Rules:

- The version text must be new for the package; you cannot reuse `0.2.0`.
- BaNaNaS rejects a file identical to one already uploaded. Always build
  from a bumped version.
- Older versions stay available for savegames. That is expected.

## Troubleshooting

| Problem | Fix |
|---|---|
| Tests fail with "must have version: …" | Make the three version places agree (step 2). |
| Release workflow: "Tag … does not match VERSION" | Delete the tag (`git push --delete origin v0.2.0`, `git tag -d v0.2.0`) and tag the right version. |
| `nmlc not found` | Install the build requirements (step 3). |
| BaNaNaS says the ID belongs to someone else | You uploaded the Hebrew GRF; see the table at the top. |
| Hebrew shows as boxes or `?` | Turn off "Use traditional sprite font" in OpenTTD. |
| GRF not in NewGRF Settings | Click **Rescan files**; make sure the `.grf` is inside the `newgrf` folder or a subfolder of it. |
