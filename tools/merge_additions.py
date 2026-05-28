"""
Merge geocoded additions into places_post_cut.json, write final places.json
and places_data.js.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
kept = json.loads((HERE / "places_post_cut.json").read_text(encoding="utf-8"))
pending = json.loads((HERE / "additions_pending.json").read_text(encoding="utf-8"))
geocoded = json.loads((HERE / "additions_geocoded.json").read_text(encoding="utf-8"))

merged_new = []
for a in pending:
    coords = geocoded.get(a["name_en"])
    if not coords:
        print(f"SKIP (no geocode): {a['name_en']}")
        continue
    place = {
        "type":        a.get("type") or "Other",
        "name_kr":     a.get("name_kr") or None,
        "name_en":     a.get("name_en"),
        "address":     a.get("address") or "",
        "notes":       a.get("notes") or "",
        "region":      a.get("region") or "Seoul",
        "source":      a.get("source") or "sheet_update_2026-04-23",
        "geocode_query": coords.get("query"),
        "lat":         coords["lat"],
        "lng":         coords["lng"],
    }
    if a.get("naver_url"):
        place["naver_url"] = a["naver_url"]
    if a.get("google_url"):
        place["google_url"] = a["google_url"]
    if a.get("web_link"):
        place["web_link"] = a["web_link"]
    merged_new.append(place)

final = kept + merged_new
print(f"Kept: {len(kept)}  Added: {len(merged_new)}  Total: {len(final)}")

(ROOT / "places.json").write_text(
    json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8"
)
js = "const PLACES = " + json.dumps(final, ensure_ascii=False, indent=2) + ";\n"
(WEB / "places_data.js").write_text(js, encoding="utf-8")
print("places.json + places_data.js rewritten")

# Region breakdown
from collections import Counter
region_counts = Counter(p.get("region") for p in final)
print()
print("Region breakdown:")
for r, c in region_counts.most_common():
    print(f"  {r:30s} {c}")
