"""Merge the geocoded Jeju restaurants into places.json + regenerate places_data.js."""
import json
import shutil
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
WEB = ROOT / "web"

geo = json.loads((HERE / "jeju_restaurants_geocoded.json").read_text(encoding="utf-8"))
# Avec found in a follow-up run — patch it in
geo["Avec (vegan)"] = {"lat": 33.4826087, "lng": 126.3969007, "query": "Avec vegan Jeju City Korea"}

ENTRIES = [
    ("앤드유 카페", "And Yu Cafe (vegan)", "Restaurant",
     "제주특별자치도 제주시 한림읍 한림로 518",
     "All-vegan (safe: no pork/shellfish/meat+milk). Bean burgers, 'chicken' nuggets, chickpea curry, cakes. Closed Tue-Wed; 12-3 / 5-9 — call ahead. ~20 min from Browncabin, pairs with Hyeopjae Beach"),
    ("다소니", "Dasoni (temple food)", "Restaurant",
     "제주시 (한옥 사찰음식)",
     "All-vegan temple food in a hanok — lotus rice, perilla sujebi, bibimbap. The 'nice dinner' pick when in Jeju City"),
    ("칠분의 오", "Five Seventh (vegan)", "Restaurant",
     "제주시",
     "All-vegan — vegan chicken (dudumchic), tteokbokki, pasta, burgers, cakes. Fri-Tue 12-7, Wed 12-4. NE side of island"),
    ("란스키친", "Lan's Kitchen (vegan)", "Restaurant",
     "제주시 (북서부)",
     "All-vegan Korean + Vietnamese, friendly owner"),
    ("아베끄", "Avec (vegan)", "Restaurant",
     "제주시 서부 (애월 방면)",
     "All-vegan Western — open sandwiches, bean burgers, pastas (~$13/dish)"),
    ("라즈마할", "Rajmahal Indian Restaurant", "Restaurant",
     "제주시",
     "Indian — chana masala, dahl, veg biryani; vegan on request. CAUTION: ask about peanut/cashew in curries. Daily 11:30-23:00"),
    ("타코맛심", "Taco Massim", "Restaurant",
     "제주시 구좌읍",
     "Mexican with vegan options, English-speaking owner. Daily 12-8. East side — only if doing an east-island day"),
    ("제주광해 애월", "Jeju Gwanghae (hairtail)", "Restaurant",
     "제주시 애월읍 애월해안로 867",
     "Grilled + braised hairtail (fin fish — safe), ocean-view on the Aewol coastal road. Daily 10-20. Ask 조개류·새우 빼주세요 for braises; skip kimchi (shrimp jeotgal)"),
    ("갈치바다", "Galchi Bada (hairtail)", "Restaurant",
     "제주시 애월읍 애월로 15-1",
     "Whole grilled hairtail with bones removed — best with kids. Mild braise. Daily 10-21, parking, reservations. Same shellfish/banchan cautions"),
    ("애월 갈치 암행어사", "Galchi Amhaengeosa (hairtail)", "Restaurant",
     "제주시 애월읍",
     "Whole braised hairtail specialist. Year-round 11-21:30. Same shellfish/banchan cautions"),
]

src = ROOT / "places.json"
shutil.copy2(src, HERE / "places.prev.json")
places = json.loads(src.read_text(encoding="utf-8"))

existing_en = {(p.get("name_en") or "").lower() for p in places}
added = 0
for kr, en, ptype, addr, notes in ENTRIES:
    g = geo.get(en)
    if not g:
        print(f"SKIP (no geocode): {en}")
        continue
    if en.lower() in existing_en:
        print(f"SKIP (already present): {en}")
        continue
    places.append({
        "type": ptype,
        "name_kr": kr,
        "name_en": en,
        "address": addr,
        "google_url": f"https://www.google.com/maps/search/?api=1&query={kr.replace(' ', '+')}",
        "naver_url": f"https://map.naver.com/p/search/{kr}",
        "notes": notes,
        "region": "Jeju",
        "source": "diet_research_2026-06-19",
        "geocode_query": g["query"],
        "geocode_source": "google_maps_playwright",
        "lat": g["lat"],
        "lng": g["lng"],
    })
    added += 1
    print(f"ADD  {en:40s} {g['lat']:.5f},{g['lng']:.5f}")

src.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
js = "const PLACES = " + json.dumps(places, ensure_ascii=False, indent=2) + ";\n"
(WEB / "places_data.js").write_text(js, encoding="utf-8")
print(f"\nAdded {added}. Total: {len(places)}")
