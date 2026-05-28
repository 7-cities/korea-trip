"""Build a worklist of failed places with the URLs to navigate."""
import json
import urllib.parse
from pathlib import Path

HERE = Path(__file__).parent
failed = json.loads((HERE / "places_failed.json").read_text(encoding="utf-8"))

worklist = []
for p in failed:
    # query: prefer Korean name + address (most accurate); else address; else name
    if p.get("address"):
        q = p["address"]
    elif p.get("name_kr"):
        q = p["name_kr"] + (" 제주" if p.get("region") == "Jeju" else "")
    else:
        q = (p.get("name_en") or "") + " South Korea"
    url = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q)
    worklist.append({
        "name_en": p["name_en"],
        "name_kr": p["name_kr"],
        "query": q,
        "url": url,
        "place_index": failed.index(p),
    })

(HERE / "recovery_worklist.json").write_text(
    json.dumps(worklist, ensure_ascii=False, indent=2), encoding="utf-8"
)
# init empty results file if missing
results_path = HERE / "recovery_results.json"
if not results_path.exists():
    results_path.write_text("{}", encoding="utf-8")

print(f"Worklist: {len(worklist)} places")
