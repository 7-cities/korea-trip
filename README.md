# Korea Trip 2026 — Interactive Map

Family trip to Korea (Jun 20 – Jul 17, 2026). This repo hosts the interactive POI map
and the Python sync tooling that keeps it in step with the planning Google Sheet.

## Live site

**https://korea-trip-ecru.vercel.app**

Deployed on Vercel as a static PWA. On phone, use the browser's "Add to Home Screen"
to install it like a native app — works offline once visited.

Project: `michael-tarrs-projects/korea-trip` on Vercel — connected to this repo for auto-deploy on push to `main`.

## Layout

```
.
├── places.json                  # Canonical POI data (source of truth)
├── vercel.json                  # Vercel config (outputDirectory: web/)
├── web/                         # Static site — deployed by Vercel
│   ├── index.html
│   ├── places_data.js           # Generated from places.json
│   ├── manifest.webmanifest
│   ├── sw.js
│   └── icon-*.png, favicon.svg
└── tools/                       # Sheet-sync workflow (not deployed)
    ├── decode_xlsx.py           # 1. fetch latest sheet.xlsx from Drive
    ├── extract_hyperlinks.py    # 2. -> tools/sheet_hyperlinks.json
    ├── final_diff.py            # 3. classify rows: exact / rename / new / cut
    ├── geocode_*.py             # 4. geocode new POIs via Playwright
    ├── apply_updates.py         # 5. patch existing places.json entries
    ├── add_gyeongju_pois.py     # 5b. append new POIs
    └── json_to_js.py            # 6. regenerate web/places_data.js
```

## Sync workflow (when the sheet changes)

```bash
cd tools
python decode_xlsx.py             # save latest xlsx (from Drive download)
python extract_hyperlinks.py      # parse xlsx -> sheet_hyperlinks.json
python final_diff.py              # see what's new / renamed / cut
# … make manual edits to places.json or run a script that applies them …
python json_to_js.py              # regenerate web/places_data.js
git add places.json web/places_data.js
git commit -m "Sync from sheet YYYY-MM-DD"
git push                          # Vercel auto-deploys
```
