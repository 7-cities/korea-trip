"""Filter extras to keepers (drop junk + dups), join with geocoded coords."""
import json
from pathlib import Path

HERE = Path(__file__).parent
extras = json.loads((HERE / "extras_to_geocode.json").read_text(encoding="utf-8"))
geo = json.loads((HERE / "extras_geocoded.json").read_text(encoding="utf-8"))

DROP = {
    # junk
    "Han River via Subway", "Comicbook cafe", "Goguma Latte", "Goguma Pizza",
    "Namsan (schedule of performances)", "Lego themed cafe in Dongdaemun design place",
    "beads for design at Dongdaemun design plaza", "Seoul Bus Tour",
    "hotel buffet", "사물놀이? 이날치?",
    # dups
    "Gwangjang Shijang", "Namsangol (Korean folk village)", "Namsan Tower",
    "Netmarble Gaming Museum", "수원스타필드 도서관", "Suwon City Walls",
}

keepers = []
for p in extras:
    if p["name_en"] in DROP:
        continue
    g = geo.get(p["name_en"])
    if not g:
        print(f"  no geocode for {p['name_en']!r}, skipping")
        continue
    p = dict(p)
    p["lat"] = g["lat"]
    p["lng"] = g["lng"]
    p["geocode_query"] = g["query"]
    p["geocode_source"] = "google_maps_playwright"
    keepers.append(p)

(HERE / "extras_keepers.json").write_text(
    json.dumps(keepers, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"Keepers: {len(keepers)} (dropped {len(extras) - len(keepers)})")
print("\nList:")
for i, p in enumerate(keepers):
    print(f"  {i:2d}: {p['name_en']}")
