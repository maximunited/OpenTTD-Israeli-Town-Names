# Contributing

- Keep the Hebrew GRF ID (`ZH\01\01`) unchanged; it belongs to the original BaNaNaS package.
  Never change a published GRF ID.
- Add full-name English corrections to the JSON data files, not a word-by-word transliterator.
- For a spelling change, include the Hebrew name, the preferred English spelling, a source,
  and whether it fixes a wrong place or only picks a spelling variant.
- Only real towns and villages belong in `israel.nml`; see [docs/NAME_DATA.md](docs/NAME_DATA.md).
- Changing the town list or any English name needs a version bump
  ([docs/PUBLISHING.md](docs/PUBLISHING.md)).
- Run `python -m unittest discover -s tests` and `python build.py` before submitting.
- Add regression tests for parser changes, especially escaped quotes and comments.
- Do not commit compiled GRFs, `dist/`, credentials or generated review reports.
- Contributions are licensed under GPL v2.
