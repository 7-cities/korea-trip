"""Merge recovered coords into places.json, then regenerate places_data.js."""
import json
from pathlib import Path

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
places = json.loads((ROOT / "places.json").read_text(encoding="utf-8"))
failed  = json.loads((HERE / "places_failed.json").read_text(encoding="utf-8"))
results = json.loads((HERE / "recovery_results.json").read_text(encoding="utf-8"))

# Build lookup: name_en -> recovered coords
recovered = []
still_failed = []
for p in failed:
    r = results.get(p["name_en"])
    if r and r.get("lat") is not None:
        p["lat"] = r["lat"]
        p["lng"] = r["lng"]
        p["geocode_query"] = r["query"]
        p["geocode_source"] = "google_maps_playwright"
        recovered.append(p)
    else:
        still_failed.append(p)

merged = places + recovered
(ROOT / "places.json").write_text(
    json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
)
(HERE / "places_failed.json").write_text(
    json.dumps(still_failed, ensure_ascii=False, indent=2), encoding="utf-8"
)
js = "const PLACES = " + json.dumps(merged, ensure_ascii=False, indent=2) + ";\n"
(WEB / "places_data.js").write_text(js, encoding="utf-8")

print(f"places.json:    {len(merged)} (was {len(places)}, +{len(recovered)})")
print(f"still failed:   {len(still_failed)}")
print(f"places_data.js: {len(merged)} entries written")
