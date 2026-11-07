# Israeli Town Names for OpenTTD

Real Israeli town names for [OpenTTD](https://www.openttd.org), in Hebrew and English.

Based on the original Hebrew set by [ZvikaZ](https://github.com/ZvikaZ/OpenTTD-Israeli-Town-Names).

## Variants

| NewGRF | Town name styles | GRF ID |
|---|---|---|
| Israeli Town Names (English) | Israeli (English) | `MA\01\01` |
| Israeli Town Names (Hebrew + English) | Israeli (Hebrew), Israeli (English) | `MA\01\02` |
| Israeli town names (original Hebrew set) | Israeli | `ZH\01\01` |

## For players

1. In OpenTTD, open **Online Content**, search for "Israeli" and download a set.
2. Activate it in **NewGRF Settings**.
3. Start a new game and choose the Israeli style in the **Town names** list.

The style is chosen per game when the map is created. If Hebrew letters show
as boxes, turn off **Use traditional sprite font** in Game Options > Graphics.

## For maintainers

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe build.py
```

`build.py` generates the English and bilingual NML, compiles all three GRFs
with `nmlc`, and writes ready-to-upload folders and zips to `dist/`. CI does
the same on every pull request and attaches the results as artifacts.

- [docs/PUBLISHING.md](docs/PUBLISHING.md): versioning, releases and uploading to BaNaNaS.
- [docs/NAME_DATA.md](docs/NAME_DATA.md): town list, English spellings and the CBS locality refresh.
- [CONTRIBUTING.md](CONTRIBUTING.md): how to propose changes.

## License

[GPL v2](LICENSE), the same license as the original release on BaNaNaS.
