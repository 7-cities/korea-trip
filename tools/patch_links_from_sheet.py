"""
Walk sheet_hyperlinks.json and attach recovered URLs to places.json:
  - URL contains naver.me OR map.naver.com  ->  naver_url
  - URL contains google.com/maps            ->  skip (already in google_url)
  - any other URL                           ->  web_link (don't overwrite if set)

Match places by name_kr first, then name_en (case-insensitive, trimmed).
"""
import json
from pathlib import Path
from collections import Counter

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
rows = json.loads((HERE / "sheet_hyperlinks.json").read_text(encoding="utf-8"))
places = json.loads((ROOT / "places.json").read_text(encoding="utf-8"))


def norm(s):
    return (s or "").strip().lower()


# Build (name_kr, name_en) -> place index map.  Some places have only one of the two.
by_kr = {}
by_en = {}
for i, p in enumerate(places):
    if p.get("name_kr"):
        by_kr.setdefault(p["name_kr"].strip(), []).append(i)
    if p.get("name_en"):
        by_en.setdefault(norm(p["name_en"]), []).append(i)


def find_place(values):
    """Try to find a single matching place from a row's values."""
    # values columns vary by sheet — name_kr is usually one of cols [1,2], name_en next.
    candidates = []
    for v in values[:5]:  # most candidate names live in first few cols
        if not v or not isinstance(v, str):
            continue
        v = v.strip()
        if v in by_kr:
            candidates.extend(by_kr[v])
        nv = norm(v)
        if nv in by_en:
            candidates.extend(by_en[nv])
    # Dedup, keep first
    seen = []
    for c in candidates:
        if c not in seen:
            seen.append(c)
    return seen


added_naver = 0
added_web   = 0
matched_rows = 0
unmatched = []

for r in rows:
    if not r["links"]:
        continue
    idxs = find_place(r["values"])
    if not idxs:
        unmatched.append((r["sheet"], r["row"], r["values"][:4]))
        continue
    matched_rows += 1
    for url in r["links"].values():
        u = url.strip()
        ul = u.lower()
        if "naver.me" in ul or "map.naver.com" in ul:
            for i in idxs:
                if not places[i].get("naver_url"):
                    places[i]["naver_url"] = u
                    added_naver += 1
        elif "google.com/maps" in ul:
            continue  # we already have google_url for these
        else:
            for i in idxs:
                if not places[i].get("web_link"):
                    places[i]["web_link"] = u
                    added_web += 1

print(f"matched rows: {matched_rows}, unmatched: {len(unmatched)}")
print(f"+naver_url: {added_naver}")
print(f"+web_link:  {added_web}")
print()
print("First 10 unmatched (need investigation):")
for s, r, vals in unmatched[:10]:
    print(f"  [{s}] row{r}: {vals}")

# Coverage report
total = len(places)
print()
print(f"places.json totals ({total}):")
print(f"  google_url: {sum(1 for p in places if p.get('google_url'))}")
print(f"  naver_url:  {sum(1 for p in places if p.get('naver_url'))}")
print(f"  web_link:   {sum(1 for p in places if p.get('web_link'))}")

jeju = [p for p in places if p.get("region") == "Jeju"]
print(f"Jeju ({len(jeju)}):")
print(f"  google_url: {sum(1 for p in jeju if p.get('google_url'))}")
print(f"  naver_url:  {sum(1 for p in jeju if p.get('naver_url'))}")
print(f"  web_link:   {sum(1 for p in jeju if p.get('web_link'))}")

(ROOT / "places.json").write_text(
    json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8"
)
js = "const PLACES = " + json.dumps(places, ensure_ascii=False, indent=2) + ";\n"
(WEB / "places_data.js").write_text(js, encoding="utf-8")
print("\nplaces.json + places_data.js rewritten")
