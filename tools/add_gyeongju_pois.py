"""Append 3 Gyeongju POIs (솔거미술관, 대릉원, 첨성대) to places.json and rebuild places_data.js."""
import json
import shutil
from pathlib import Path

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
src = ROOT / "places.json"
shutil.copy2(src, HERE / "places.prev.json")

places = json.loads(src.read_text(encoding="utf-8"))
g = json.loads((HERE / "gyeongju_geocoded.json").read_text(encoding="utf-8"))

NEW = [
    {
        "type": "Museum",
        "name_kr": "솔거미술관",
        "name_en": "Sulgeo Art Museum",
        "address": "경상북도 경주시 신평동 1097-1",
        "google_url": "https://www.google.com/maps/search/?api=1&query=솔거미술관+경주",
        "naver_url": "https://map.naver.com/p/search/솔거미술관",
        "notes": "Day 1 stop",
        "region": "Gyeongsangbuk-do",
        "source": "sheet_update_2026-05-27",
        "geocode_query": g["sulgeo_art_museum"]["query"],
        "geocode_source": "google_maps_playwright",
        "lat": g["sulgeo_art_museum"]["lat"],
        "lng": g["sulgeo_art_museum"]["lng"],
    },
    {
        "type": "Culture",
        "name_kr": "대릉원",
        "name_en": "Daereungwon Tomb Complex",
        "address": "경상북도 경주시 황남동 31-1",
        "google_url": "https://www.google.com/maps/search/?api=1&query=대릉원+경주",
        "naver_url": "https://map.naver.com/p/search/대릉원",
        "notes": "Day 2 stop — Silla royal tombs",
        "region": "Gyeongsangbuk-do",
        "source": "sheet_update_2026-05-27",
        "geocode_query": g["daereungwon"]["query"],
        "geocode_source": "google_maps_playwright",
        "lat": g["daereungwon"]["lat"],
        "lng": g["daereungwon"]["lng"],
    },
    {
        "type": "Culture",
        "name_kr": "첨성대",
        "name_en": "Cheomseongdae Observatory",
        "address": "경상북도 경주시 인왕동 839-1",
        "google_url": "https://www.google.com/maps/search/?api=1&query=첨성대+경주",
        "naver_url": "https://map.naver.com/p/search/첨성대",
        "notes": "Day 2 stop — 7th-century stone observatory",
        "region": "Gyeongsangbuk-do",
        "source": "sheet_update_2026-05-27",
        "geocode_query": g["cheomseongdae"]["query"],
        "geocode_source": "google_maps_playwright",
        "lat": g["cheomseongdae"]["lat"],
        "lng": g["cheomseongdae"]["lng"],
    },
]

places.extend(NEW)
src.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
js = "const PLACES = " + json.dumps(places, ensure_ascii=False, indent=2) + ";\n"
(WEB / "places_data.js").write_text(js, encoding="utf-8")

print(f"Added {len(NEW)} POIs. Total now: {len(places)}")
for p in NEW:
    print(f"  + {p['name_kr']} / {p['name_en']} @ {p['lat']:.5f}, {p['lng']:.5f}")
