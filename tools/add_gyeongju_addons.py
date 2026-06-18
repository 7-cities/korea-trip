"""Append 3 more Gyeongju POIs to places.json."""
import json
import shutil
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
WEB = ROOT / "web"

src = ROOT / "places.json"
shutil.copy2(src, HERE / "places.prev.json")

places = json.loads(src.read_text(encoding="utf-8"))
g = json.loads((HERE / "gyeongju_addons_geocoded.json").read_text(encoding="utf-8"))

NEW = [
    {
        "type": "Heritage",
        "name_kr": "계림",
        "name_en": "Gyerim Forest",
        "address": "경상북도 경주시 교동 1",
        "google_url": "https://www.google.com/maps/search/?api=1&query=계림+경주",
        "naver_url": "https://map.naver.com/p/search/계림",
        "notes": "Sacred Silla forest between Cheomseongdae and Woljeonggyo — Day 2 coffee-break stroll",
        "region": "Gyeongsangbuk-do",
        "source": "agenda_update_2026-06-16",
        "geocode_query": g["gyerim"]["query"],
        "geocode_source": "google_maps_playwright",
        "lat": g["gyerim"]["lat"],
        "lng": g["gyerim"]["lng"],
    },
    {
        "type": "Heritage",
        "name_kr": "월정교",
        "name_en": "Woljeonggyo Bridge",
        "address": "경상북도 경주시 교동 274",
        "google_url": "https://www.google.com/maps/search/?api=1&query=월정교+경주",
        "naver_url": "https://map.naver.com/p/search/월정교",
        "notes": "Restored Silla-era stone bridge — pairs with Gyerim on Day 2 afternoon",
        "region": "Gyeongsangbuk-do",
        "source": "agenda_update_2026-06-16",
        "geocode_query": g["woljeonggyo"]["query"],
        "geocode_source": "google_maps_playwright",
        "lat": g["woljeonggyo"]["lat"],
        "lng": g["woljeonggyo"]["lng"],
    },
    {
        "type": "Nature & Culture",
        "name_kr": "경주엑스포대공원",
        "name_en": "Gyeongju Expo Grand Park",
        "address": "경상북도 경주시 신평동 1095",
        "google_url": "https://www.google.com/maps/search/?api=1&query=경주엑스포대공원",
        "naver_url": "https://map.naver.com/p/search/경주엑스포대공원",
        "notes": "Large park at Bomun Lake — Day 1 afternoon walk after Sulgeo Art Museum",
        "region": "Gyeongsangbuk-do",
        "source": "agenda_update_2026-06-16",
        "geocode_query": g["gyeongju_expo_park"]["query"],
        "geocode_source": "google_maps_playwright",
        "lat": g["gyeongju_expo_park"]["lat"],
        "lng": g["gyeongju_expo_park"]["lng"],
    },
]

places.extend(NEW)
src.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
js = "const PLACES = " + json.dumps(places, ensure_ascii=False, indent=2) + ";\n"
(WEB / "places_data.js").write_text(js, encoding="utf-8")

print(f"Added {len(NEW)} POIs. Total: {len(places)}")
for p in NEW:
    print(f"  + {p['name_kr']} / {p['name_en']} @ {p['lat']:.5f}, {p['lng']:.5f}")
