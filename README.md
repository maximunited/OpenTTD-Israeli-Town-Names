# Israeli Town Names for OpenTTD

Originally created by ZvikaZ: https://github.com/ZvikaZ/OpenTTD-Israeli-Town-Names

The original Hebrew NewGRF is preserved. This fork adds tooling for a separate English variant, with its own GRFID and town-name style.

## Status and translation quality

The Hebrew source is buildable directly. The English generator requires translation data: your existing `english_names_cache.json` and optional `english_name_overrides.json`. These are not bundled here. A fresh clone cannot yet build the full English set without supplying translations. CI builds Hebrew only; it does not claim to validate an English name database.

Cached English labels are unverified candidates, not authoritative locality matches. Identical Hebrew labels can refer to unrelated entities. Review the bilingual CSV before publishing. No automatic transliteration or live Wikidata lookup is performed. Missing names fail generation rather than silently producing bad names.

## Build (PowerShell)

Install Python 3.12 or newer, then from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\nmlc.exe -c --grf israeli_town_names_hebrew.grf israel.nml
```

Using explicit virtual-environment executable paths avoids PATH and activation-policy problems. On Linux/macOS use `.venv/bin/python` and `.venv/bin/nmlc` instead.

### English variant

Place your existing cache beside `make_english.py`. Add reviewed full-name corrections in `english_name_overrides.json`, a UTF-8 JSON object:

```json
{
  "אמנון": "Amnon",
  "אפיקים": "Afikim",
  "דבוריה": "Dabburiyya",
  "ענב": "Enav",
  "גבעת חיים (איחוד)": "Givat Haim (Ihud)",
  "כפר חב\"ד": "Kfar Chabad"
}
```

Choose a consistent spelling policy; English variants do not necessarily identify different places. Manual overrides take precedence over cached labels. Duplicate JSON keys and invalid translations are rejected.

```powershell
.\.venv\Scripts\python.exe .\make_english.py
# Stop if generation failed. Do not compile stale output.
if ($LASTEXITCODE -ne 0) { throw 'English generation failed' }
.\.venv\Scripts\nmlc.exe -c --lang-dir lang_english --grf israeli_town_names_english.grf israel_english.nml
Invoke-Item .\town_names_review.csv
```

The generator handles escaped quotation marks, excludes commented-out entries, and writes a review report even when names are missing. It changes GRFID `ZH\01\01` to `ZH\01\02` without modifying the original source. The numeric GRF format version in NML and the display version in `custom_tags.txt` are separate concepts.

## Install and select

Use the installation you actually launch. Steam: Library > OpenTTD > Manage > Browse local files. Create a `newgrf` subfolder there and copy the compiled English GRF into it. Do not assume Steam is installed under Program Files. For example, using the location found on your machine:

```powershell
$grfDir = "$env:USERPROFILE\Steam\steamapps\common\OpenTTD\newgrf"
New-Item -ItemType Directory -Force $grfDir | Out-Null
Copy-Item .\israeli_town_names_english.grf $grfDir -Force
```

In OpenTTD 15.3: New Game > NewGRF Settings > Rescan files. Add `Israeli Town Names (English)` from the inactive list, then select `Israeli (English)` under Town names before generating the map. Online Content lists published downloads, not this unpublished local build. Restart the game if necessary.

Existing saved town names are not automatically translated. To ensure Jerusalem or Tel Aviv belongs to a large town, use a scenario or rename towns after generation; name-selection weights do not reserve names for large cities.

## Development

Run `python -m unittest discover -s tests -v`. Keep compiled GRFs, local caches and review reports out of commits. For a reproducible English release, contribute reviewed translation data with source/provenance notes; do not publish a cache as verified data. Preserve upstream attribution and Hebrew compatibility.

Before pulling remote changes into an existing working tree, back up or commit untracked local scripts: they may conflict with newly tracked files.

## License

No standalone license file was present in the inspected upstream tree. This fork does not assume or assign a license to upstream code or datasets. Clarify licensing and translation-data redistribution rights with the relevant authors before publishing releases.
