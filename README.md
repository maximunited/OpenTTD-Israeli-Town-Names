# Israeli Town Names for OpenTTD

Originally created by [ZvikaZ](https://github.com/ZvikaZ/OpenTTD-Israeli-Town-Names). This fork preserves the original Hebrew GRF and adds an English variant.

## Build

Python 3.12+ and Git with full history are required for the complete tests. In PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
.\.venv\Scripts\python.exe .\make_english.py
if ($LASTEXITCODE -ne 0) { throw 'Generation failed; do not compile stale output' }
.\.venv\Scripts\nmlc.exe -c --grf israeli_town_names_hebrew.grf israel.nml
if ($LASTEXITCODE -ne 0) { throw 'Hebrew build failed' }
.\.venv\Scripts\nmlc.exe -c --lang-dir lang_english --grf israeli_town_names_english.grf israel_english.nml
if ($LASTEXITCODE -ne 0) { throw 'English build failed' }
```

Linux/macOS: use `.venv/bin/python` and `.venv/bin/nmlc`. Normal generation is offline and works with the committed cache and reviewed mappings even before a CBS snapshot exists.

## Names and preferences

Priority, highest first:

1. `display_name_preferences.json` (e.g. Amnon).
2. `english_name_overrides.json` (the complete historical corrections).
3. `english_names_cache.json` (unverified cached labels).
4. Saved CBS snapshot, only unambiguous exact Hebrew-name matches for otherwise unresolved existing names.

The town-specific flag was removed. Use `--preferences path.json` or `--overrides path.json` for alternative complete mapping files. The separate preference file keeps the historical override migration independently verifiable while keeping all spelling choices in data.

`town_names_review.csv` is sorted alphabetically by English display name. The generated town-name pool retains source order; sorting the report does not reorder the pool. In-game town-directory sorting is controlled by OpenTTD.

The generator handles escaped quotation marks, excludes comments, rejects unresolved/invalid English names, and uses English GRFID `ZH\01\02` without changing original Hebrew GRFID `ZH\01\01`. Never compile stale NML after a generation failure. Rebuilding does not rename towns already stored in saves.

## Explicit CBS refresh

Official API documentation: https://www.cbs.gov.il/en/Pages/API-Dictionary.aspx

```powershell
.\.venv\Scripts\python.exe .\make_english.py --refresh-cbs
# Optional specific published vintage:
.\.venv\Scripts\python.exe .\make_english.py --refresh-cbs --cbs-year 2024
```

The fetcher uses a User-Agent, bounded retries/timeouts, pagination, duplicate detection, vintage checks, a minimum-size guard and atomic snapshot replacement. Unknown response schemas fail safely. The live response has not been verified by the authoring assistant's network tool; the first workflow execution must validate the schema and paging behavior against CBS. Do not describe this as a proven live integration until that succeeds.

A refresh writes `data/cbs_localities.json` with stable codes, data year and retrieval provenance, `data/cbs_changes.md` with changes since the previous snapshot, and `data/cbs_candidates.csv` with records not exactly matched to existing names. An initial snapshot lists all records as new candidates. Records absent from a later snapshot are NOT automatically declared obsolete.

CBS names may be uppercase or use different conventions; they are not silently title-cased. Manual corrections and preferences retain priority. Missing English names and ambiguous Hebrew matches do not silently fill unresolved entries. Every source candidate still needs name/alias/eligibility review. Normal builds do not require the API.

No new playable town, including Trump Heights, is automatically added by this fetcher. Review its code, current official name and aliases before adding it once to the existing Hebrew source and updating mappings. Government approval alone is insufficient evidence that a proposed community is inhabited. A full code-based locality/alias migration and complete obsolete-name audit remain future work.

## Scheduled review PRs

`Review CBS directory updates` runs monthly and manually. It fetches, validates, generates, compiles English, uploads review artifacts and proposes a PR with the snapshot/report. It never merges. GitHub repository settings must allow Actions to create pull requests. PRs created by the default token may not automatically trigger CI; dispatch CI manually if needed. A network/schema failure stops the workflow instead of changing the snapshot. The monthly job has write permissions; ordinary CI is read-only.

## Tests

Tests cover parser quotes/comments, full committed name coverage, historical override migration, data-driven preferences, deterministic generation, invalid translations, paging, repeated pages/duplicates, mixed vintage, schema rejection, failed-refresh preservation and ambiguous source-name matches. CI compiles both GRFs offline. Inspect the actual Actions results before asserting new code passes. Future tests should add recorded live CBS fixtures and exercise retry/HTTP behavior; mocked paging tests alone do not validate the live service.

## Install

Close OpenTTD. In Steam use Manage > Browse local files to locate the correct installation. Example:

```powershell
$grfDir = "$env:USERPROFILE\Steam\steamapps\common\OpenTTD\newgrf"
New-Item -ItemType Directory -Force $grfDir | Out-Null
Copy-Item .\israeli_town_names_english.grf $grfDir -Force
```

OpenTTD 15.3: New Game > NewGRF Settings > Rescan files, activate Israeli Town Names (English), and select Israeli (English) under Town names. Local unpublished builds do not appear in Online Content. Test a fresh map.

## Data and release limitations

Cached translations are not fully verified. Flag duplicate English names for review rather than assuming they are invalid. Stable source IDs exist in the CBS snapshot, but the current playable source remains a legacy name list. Generated files already tracked by earlier commits remain tracked despite ignore rules. Regenerate before compiling.

No standalone upstream license file was present in the inspected tree. Clarify code/data redistribution rights and attribution before publishing a release. Preserve upstream author credit. Back up local changes before pulling; do not force-reset translation work. See CONTRIBUTING.md.
