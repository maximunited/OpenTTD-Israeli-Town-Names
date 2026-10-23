# Contributing

- Keep Hebrew behavior and GRFID unchanged unless a deliberate compatibility change is discussed.
- Add full-name English corrections to translation data, not a word-by-word transliterator.
- Include the Hebrew name, preferred English spelling, source, and whether the change fixes a wrong entity or merely chooses a spelling variant.
- Do not claim every cached label is verified. Record unresolved names instead of guessing.
- Run `python -m unittest discover -s tests -v` and compile affected GRFs before submitting changes.
- Add regression tests for parser changes, especially escaped quotes and comments.
- Do not commit compiled GRFs, personal caches, credentials, or generated review reports.
- Clarify upstream and dataset licensing before distributing a release.
