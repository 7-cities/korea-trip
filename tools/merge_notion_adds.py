"""Merge curated Minjuncooks Notion additions into places.json."""
import json
import shutil
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
WEB = ROOT / "web"

geo = json.loads((HERE / "notion_adds_geocoded.json").read_text(encoding="utf-8"))

# (geo_key, name_kr, name_en, address, notes)  -- Avec already present, skip (location confirmed)
ENTRIES = [
    ("assalam", "아살람 레스토랑", "As-Salam (halal Arab)",
     "제주시 중앙로2길 7 1층",
     "Halal Arab — falafel wraps (Minjuncooks' top pick here). No pork/shellfish; chickpea-based, kid-friendly. Jeju City center"),
    ("sumbida", "숨비다", "Sumbida (vegan options)",
     "제주시 애월읍 애월로 118 2층",
     "Aewol town, ~10 min from Browncabin. Has vegan options (not all-vegan) — confirm dish before ordering"),
    ("baram", "비건테이블바람", "Vegan Table Baram [ALL Vegan]",
     "제주시 애월읍 납읍동1길 18-14",
     "ALL vegan — inherently safe (no pork/shellfish/milk). Napeup village, Aewol-eup, close to base. Verify current hours before going"),
    ("fengohoda", "펜고호다", "Fengohoda [ALL Vegan cafe]",
     "제주시 애월읍 봉성로 61 1층",
     "ALL-vegan dessert cafe — no milk/butter/egg/refined sugar. Beautiful slice cakes. Aewol-eup, close to base. IG @pengohoda (active 2026)"),
    ("jeju_vegies", "제주베지스", "Jeju Vegies [ALL Vegan]",
     "서귀포시 안덕면 녹차분재로 568 (near O'sulloc)",
     "ALL vegan — hallabong vegan sweet-&-sour is the signature (Minjuncooks callout). Near O'sulloc tea fields, south — pairs with a south-island day"),
    ("dubu_hyeopjae", "두부 제주협재점", "Dubu Hyeopjae (tofu)",
     "제주시 한림읍 협재10길 14",
     "Tofu restaurant at Hyeopjae — walkable to the beach + Hallim Park + And Yu. Tofu-centered, ask to confirm no shellfish in stew"),
    ("loving_hut", "러빙헛 서귀포점", "Loving Hut Seogwipo [ALL Vegan]",
     "서귀포시 일주동로 7036",
     "ALL-vegan Korean (reliable global vegan chain) — guaranteed safe. Seogwipo, for a south-island day"),
    ("yuyeonhan_baker", "유연한베이커", "The Flexible Baker [ALL Vegan]",
     "서귀포시 안덕면 사계중앙로 48",
     "ALL-vegan bakery — 'really delicious vegan bread' (Minjuncooks callout). Sagye, south coast near Sanbangsan"),
    ("ppang_sagye", "빵사계", "Ppang Sagye [ALL Vegan bakery]",
     "서귀포시 향교로 151",
     "ALL-vegan bakery. Seogwipo — south-day option"),
    ("salady_nohyeong", "샐러디 제주노형점", "Salady Nohyeong (salad)",
     "제주시 연북로 24 103호",
     "Salad chain — easy safe build-your-own. Nohyeong, Jeju City. Skip creamy dressings if avoiding milk"),
    ("yuinwon", "유인원", "Yuinwon (cafe)",
     "서귀포시 무영로254번길 17",
     "Cafe run by a zoologist — quirky research displays, sells vegan yogurt. Fun kid stop on a south-island day"),
]

src = ROOT / "places.json"
shutil.copy2(src, HERE / "places.prev.json")
places = json.loads(src.read_text(encoding="utf-8"))
existing_en = {(p.get("name_en") or "").lower() for p in places}

added = 0
for key, kr, en, addr, notes in ENTRIES:
    g = geo.get(key)
    if not g:
        print(f"SKIP (no geocode): {en}")
        continue
    if en.lower() in existing_en:
        print(f"SKIP (present): {en}")
        continue
    places.append({
        "type": "Restaurant",
        "name_kr": kr,
        "name_en": en,
        "address": addr,
        "google_url": f"https://www.google.com/maps/search/?api=1&query={kr.replace(' ', '+')}",
        "naver_url": f"https://map.naver.com/p/search/{kr}",
        "notes": notes,
        "region": "Jeju",
        "source": "minjuncooks_notion_2026-06-19",
        "geocode_query": g["query"],
        "geocode_source": "google_maps_playwright",
        "lat": g["lat"],
        "lng": g["lng"],
    })
    added += 1
    print(f"ADD  {en:42s} {g['lat']:.5f},{g['lng']:.5f}")

src.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
js = "const PLACES = " + json.dumps(places, ensure_ascii=False, indent=2) + ";\n"
(WEB / "places_data.js").write_text(js, encoding="utf-8")
print(f"\nAdded {added}. Total: {len(places)}")
