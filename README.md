# Israeli Town Names for OpenTTD

Originally created by [ZvikaZ](https://github.com/ZvikaZ/OpenTTD-Israeli-Town-Names). This fork preserves the original Hebrew NewGRF and adds a separate English variant.

## Translation data and status

The repository includes `english_names_cache.json`, contributed in commit `352c8d9`, and `english_name_overrides.json`, migrated from that commit's complete `NAME_OVERRIDES` dictionary. Overrides win over cached labels. The migration test compares the JSON against the historical Python literal, without executing historical code.

Cached labels remain unverified candidates, not an authoritative gazetteer. The overrides preserve previous corrections; migration does not certify every spelling. Review `town_names_review.csv` before releasing. No network lookup or automatic transliteration is performed. Missing names fail generation instead of being guessed.

## Build on Windows (PowerShell)

Use Python 3.12 or newer. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
.\.venv\Scripts\python.exe .\make_english.py --amnon
if ($LASTEXITCODE -ne 0) { throw 'Generation failed; do not compile stale output' }
.\.venv\Scripts\nmlc.exe -c --grf israeli_town_names_hebrew.grf israel.nml
if ($LASTEXITCODE -ne 0) { throw 'Hebrew build failed' }
.\.venv\Scripts\nmlc.exe -c --lang-dir lang_english --grf israeli_town_names_english.grf israel_english.nml
if ($LASTEXITCODE -ne 0) { throw 'English build failed' }
```

Explicit executable paths avoid PATH and PowerShell activation-policy issues. On Linux/macOS use `.venv/bin/python` and `.venv/bin/nmlc`.

`--amnon` selects the spelling Amnon for אמנון. Omit it to use the data's spelling. The CLI spelling preference wins over cache and JSON overrides. For other corrections, edit `english_name_overrides.json`, or pass `--overrides path/to/alternative.json` to replace the default override file.

The generator handles escaped quotes and ignores commented-out entries. It changes only the generated variant's identity from `ZH\01\01` to `ZH\01\02` and renames the internal `real` block. Original Hebrew source remains unchanged. NML GRF version fields and display versions in `custom_tags.txt` serve different purposes.

## Review

```powershell
Invoke-Item .\town_names_review.csv
```

The report distinguishes manual overrides, unverified cached labels, CLI spelling preferences and unresolved names. Successful generation checks coverage, not factual correctness of every locality match. Add the Hebrew name, English spelling and source when proposing corrections.

## Install

Use the installation you actually launch. In Steam choose Manage > Browse local files, create its `newgrf` directory and copy the English GRF there. Example for the installation used during development:

```powershell
$grfDir = "$env:USERPROFILE\Steam\steamapps\common\OpenTTD\newgrf"
New-Item -ItemType Directory -Force $grfDir | Out-Null
Copy-Item .\israeli_town_names_english.grf $grfDir -Force
```

In OpenTTD 15.3, open New Game > NewGRF Settings > Rescan files. Add Israeli Town Names (English), return to world generation and choose Israeli (English) under Town names. Online Content does not list unpublished local builds. Restart if necessary.

Existing saved town names are not automatically translated. Name weights cannot reserve Jerusalem or Tel Aviv for large towns; use scenarios or rename towns after generation.

## Tests and CI

Run `python -m unittest discover -s tests -v`. The historical migration test requires Git and full history; shallow clones should fetch the historical commit first. CI checks out full history, runs parser and integration tests, regenerates English with `--amnon`, compiles both GRFs and uploads them with the review CSV. Consult the actual Actions result before claiming the current build passes.

Some generated reports and NML were already tracked in the initial English commit. Ignore rules do not untrack those files. Regenerate English before compiling; tracked generated output can lag behind the source/data. The existing cache is retained for reproducibility, not treated as reviewed data.

Before pulling into your existing working tree, commit or back up local edits and untracked files. Do not force-reset away local translation work.

## License and attribution

No standalone license file was present in the inspected upstream tree. Do not infer a license for upstream code or redistribute datasets without clarifying applicable rights and attribution. Preserve upstream author credit. See CONTRIBUTING.md for contribution practices.
