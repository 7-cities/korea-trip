"""Apply the 3 RENAME/UPDATE patches to places.json and regenerate places_data.js."""
import json
import shutil
from pathlib import Path

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
# Back up first
src = ROOT / "places.json"
backup = HERE / "places.prev.json"
shutil.copy2(src, backup)
print(f"Backup -> {backup.name}")

places = json.loads(src.read_text(encoding="utf-8"))
geocoded = json.loads((HERE / "rename_geocoded.json").read_text(encoding="utf-8"))

updates_applied = 0


def patch(p):
    """Apply patch dict to place dict, only setting keys that are not None."""
    global updates_applied
    for k, v in p.items():
        if v is not None:
            place[k] = v
    updates_applied += 1


# --- 1) Seoul Grand Park: split name into kr + clean en, add address/links/notes ---
for place in places:
    if place.get("name_en") == "Seoul Grand Park (zoo and botanical garden)":
        place["name_kr"] = "서울대공원"
        place["name_en"] = "Seoul Grand Park"
        place["type"] = "Theme Park"
        place["address"] = "경기도 과천시 막계동 159-1"
        place["notes"] = "Zoo and botanical garden"
        place["region"] = "Gyeonggi"
        place["naver_url"] = "https://naver.me/G2Ew30d2"
        place["google_url"] = "https://www.google.com/maps/search/?api=1&query=경기도+과천시+막계동+159-1"
        updates_applied += 1
        print(f"Updated Seoul Grand Park: name_kr=서울대공원, region=Gyeonggi")
        break

# --- 2) Nanta -> Myeongdong Nanta Theater (re-geocoded) ---
for place in places:
    if place.get("name_en") == "Nanta" and place.get("name_kr") == "난타공연":
        coords = geocoded.get("myeongdong_nanta")
        place["name_kr"] = "명동난타극장"
        place["name_en"] = "Myeongdong Nanta Theater"
        place["type"] = "Performance"
        place["address"] = "서울특별시 중구 명동2가 50-14 유네스코회관 3층"
        place["naver_url"] = "https://map.naver.com/p/search/명동난타극장"
        place["google_url"] = "https://www.google.com/maps/search/?api=1&query=서울특별시+중구+명동2가+50-14+유네스코회관+3층"
        if coords:
            place["lat"] = coords["lat"]
            place["lng"] = coords["lng"]
            place["geocode_query"] = coords["query"]
        # keep web_link, notes
        updates_applied += 1
        print(f"Updated Nanta -> Myeongdong Nanta Theater (coords {place['lat']}, {place['lng']})")
        break

# --- 3) Mimiline -> Mimi Line Myeongdong (clean name + address) ---
for place in places:
    if place.get("name_en") == "미미라인 명동점 7번출구 (Mimiline/Shopping)":
        place["name_kr"] = "미미라인 명동점"
        place["name_en"] = "Mimi Line Myeongdong"
        place["type"] = "Shopping"
        place["address"] = "서울특별시 중구 충무로1가 24-5"
        place["naver_url"] = "https://map.naver.com/v5/search/미미라인%20명동점"
        place["google_url"] = "https://www.google.com/maps/search/?api=1&query=서울특별시+중구+충무로1가+24-5"
        # keep existing coords (sheet address within ~100m of existing pin)
        updates_applied += 1
        print(f"Updated Mimiline -> Mimi Line Myeongdong")
        break

print(f"\nTotal updates applied: {updates_applied}")

# Rewrite
src.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
js = "const PLACES = " + json.dumps(places, ensure_ascii=False, indent=2) + ";\n"
(WEB / "places_data.js").write_text(js, encoding="utf-8")
print(f"Wrote places.json ({len(places)} entries) and places_data.js")
