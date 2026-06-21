"""Append Expedia Group Korea office as a Work-category POI."""
import json
import shutil
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
WEB = ROOT / "web"

src = ROOT / "places.json"
shutil.copy2(src, HERE / "places.prev.json")

places = json.loads(src.read_text(encoding="utf-8"))
g = json.loads((HERE / "expedia_geocoded.json").read_text(encoding="utf-8"))

NEW = {
    "type": "Work",
    "name_kr": "익스피디아 그룹 코리아",
    "name_en": "Expedia Group Korea (Office)",
    "address": "서울특별시 종로구 종로5길 7, Tower 8 9층 (청진동)",
    "google_url": "https://www.google.com/maps/search/?api=1&query=타워8+종로",
    "naver_url": "https://map.naver.com/p/search/타워8",
    "notes": "Michael's office while working from Seoul (weeks 2–3)",
    "region": "Seoul",
    "source": "manual_2026-06-16",
    "geocode_query": g["query"],
    "geocode_source": "google_maps_place_url",
    "lat": g["lat"],
    "lng": g["lng"],
    "district": "종로구",
}

places.append(NEW)
src.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
js = "const PLACES = " + json.dumps(places, ensure_ascii=False, indent=2) + ";\n"
(WEB / "places_data.js").write_text(js, encoding="utf-8")

print(f"Added Expedia office. Total places: {len(places)}")
print(f"  {NEW['name_kr']} / {NEW['name_en']} @ {NEW['lat']:.5f}, {NEW['lng']:.5f}")
