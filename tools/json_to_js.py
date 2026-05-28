"""Convert places.json into places_data.js (a global PLACES const) for the HTML map."""
import json
from pathlib import Path

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
src = ROOT / "places.json"
dst = WEB / "places_data.js"

data = json.loads(src.read_text(encoding="utf-8"))
js = "const PLACES = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
dst.write_text(js, encoding="utf-8")
print(f"Wrote {len(data)} places to {dst.name}")
