# i-rekins.lv rēķinu eksports

Ielādē biedrības "Riekstu 11" komunālo rēķinu sarakstu no i-rekins.lv un pārvērš to md failos `r11/rekini/`.

## Uzstādīšana

```sh
cd tools/irekins
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Repozitorija saknē izveido `.env` (netiek commitots):

```
IREKINS_LOGIN=...
IREKINS_PASSWORD=...
IREKINS_PROJECT_ID=23      # projekts "Biedrība Riekstu 11"
IREKINS_OBJECT_ID=1161
```

## Lietošana

```sh
.venv/bin/python irekins.py run --from 2026-09 --to 2026-09   # ielādēt un konvertēt vienu mēnesi
.venv/bin/python irekins.py fetch --from 2020-01 --to 2026-08  # tikai lejupielāde
.venv/bin/python irekins.py convert                            # visi ielādētie mēneši → md
```

- Neapstrādātās lapas glabājas `temp/irekins/raw/GGGG-MM.html` (gitignorēts); jau ielādētos mēnešus `fetch` izlaiž, ja vien nav `--refresh`.
- Mēneši bez rēķiniem md failu nerada.
- `convert` pārraksta arī `r11/rekini/00_saraksts.md` ar visu mēnešu kopsummām.
