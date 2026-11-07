# Town names and English spellings

## Where names come from

- `israel.nml`: the playable town list (Hebrew). It is the source for all
  three GRFs. Only real towns and villages belong here, not tribes,
  industrial zones, camps, institutions or statistical areas.
- English spellings, highest priority first:
  1. `display_name_preferences.json`: deliberate spelling choices.
  2. `english_name_overrides.json`: reviewed corrections.
  3. `english_names_cache.json`: older labels, not all verified.
  4. CBS snapshot (`data/cbs_localities.json`): only exact, unambiguous
     Hebrew matches for names still missing a spelling.

`python make_english.py` writes `israel_english.nml`, `israel_bilingual.nml`
and `town_names_review.csv` (every town, its English name and which source
it came from, sorted by English name). Generation fails if any town has no
valid English name. Fix the data, never edit the generated NML.

## Adding or removing a town

1. Add or remove the `text("…", 1),` line in `israel.nml`.
2. For a new town, add its English spelling to `english_name_overrides.json`.
3. Run the tests, then bump the version (see [PUBLISHING.md](PUBLISHING.md)).
   Changing the list changes town names in existing saves, so the version
   bump is required.

## CBS refresh (official locality list)

The Israel Central Bureau of Statistics publishes the official locality list
([API docs](https://www.cbs.gov.il/en/Pages/API-Dictionary.aspx)).

```powershell
python make_english.py --refresh-cbs
python make_english.py --refresh-cbs --cbs-year 2024
```

A refresh writes:

- `data/cbs_localities.json`: the full snapshot (all record types).
- `data/cbs_changes.md`: towns added, missing or changed since the last snapshot.
- `data/cbs_candidates.csv`: CBS towns that are not in the playable list.

Non-towns are left out of the change report and the candidate list. They are
CBS types 460 (Bedouin tribes), 520 (industrial zones, regional centres) and
530 (statistical areas), plus names matching the markers in
`review_rules.py` (camps, schools, hospitals and similar). Type 510 mixes
real villages with institutions, so only the markers apply to it.

Nothing is added to or removed from the game automatically. A candidate is
added only after a person checks its current name and that it is inhabited.

The **Review CBS directory updates** workflow runs monthly. It refreshes the
snapshot, builds everything and opens a pull request for review; it never
merges. A failed download keeps the previous snapshot.
