"""Geocode + append the 4 hand-drawn-map POIs missing from places.json."""
import asyncio
import json
import re
import shutil
import sys
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).parent
ROOT = HERE.parent
WEB = ROOT / "web"
COORD_RE = re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)")
PLACE_RE = re.compile(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)")

ENTRIES = [
    {
        "key": "fairytale",
        "name_kr": "제주동화마을", "name_en": "Jeju Fairytale Village",
        "type": "Kids",
        "queries": ["제주 서귀포시 남원읍 태위로 236 제주동화마을", "제주동화마을 남원"],
        "address": "서귀포시 남원읍 태위로 236",
        "notes": "Storybook-themed village, kid-oriented photo spots (Day 2 south)",
    },
    {
        "key": "yongnuni",
        "name_kr": "용눈이오름", "name_en": "Yongnuni Oreum",
        "type": "Nature",
        "queries": ["제주 제주시 구좌읍 종달리 산28 용눈이오름", "용눈이오름"],
        "address": "제주시 구좌읍 종달리 산28",
        "notes": "Gentle grassy volcanic cone, easy hike, sunset views (physically east = Day 3, though drawn nearer Day 2)",
    },
    {
        "key": "bonte",
        "name_kr": "본태박물관", "name_en": "Bonte Museum",
        "type": "Museum",
        "queries": ["제주 서귀포시 안덕면 산록남로762번길 69 본태박물관", "본태박물관 안덕"],
        "address": "서귀포시 안덕면 산록남로762번길 69",
        "notes": "Modern art + traditional crafts museum, Tadao Ando architecture (Day 2 south)",
    },
    {
        "key": "haenyeo",
        "name_kr": "해녀박물관", "name_en": "Jeju Haenyeo Museum",
        "type": "Museum",
        "queries": ["제주 제주시 구좌읍 해녀박물관길 26 해녀박물관", "제주해녀박물관 구좌"],
        "address": "제주시 구좌읍 해녀박물관길 26",
        "notes": "Museum of Jeju's women free-divers (haenyeo) — next to Sehwa cafés (Cafe Hallasan, Dalcheese). Day 3 east",
    },
]


async def geocode(page, queries):
    for q in queries:
        url = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q)
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_url(re.compile(r"/maps/place/"), timeout=13000)
        except Exception:
            pass
        for _ in range(12):
            m = COORD_RE.search(page.url) or PLACE_RE.search(page.url)
            if m:
                mm = re.search(r"/maps/place/([^/]+)/", page.url)
                slug = urllib.parse.unquote(mm.group(1))[:45] if mm else "?"
                return {"lat": float(m.group(1)), "lng": float(m.group(2)), "query": q, "slug": slug}
            await asyncio.sleep(0.4)
    return None


async def main():
    src = ROOT / "places.json"
    shutil.copy2(src, HERE / "places.prev.json")
    places = json.loads(src.read_text(encoding="utf-8"))

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await (await browser.new_context(locale="en-US")).new_page()
        added = 0
        for e in ENTRIES:
            g = await geocode(page, e["queries"])
            if not g:
                print(f"FAIL {e['name_en']}")
                continue
            print(f"OK   {e['name_en']:26s} {g['lat']:.5f},{g['lng']:.5f}  slug={g['slug']}")
            places.append({
                "type": e["type"],
                "name_kr": e["name_kr"],
                "name_en": e["name_en"],
                "address": e["address"],
                "google_url": f"https://www.google.com/maps/search/?api=1&query={e['name_kr']}",
                "naver_url": f"https://map.naver.com/p/search/{e['name_kr']}",
                "notes": e["notes"],
                "region": "Jeju",
                "source": "handmap_2026-06-19",
                "geocode_query": g["query"],
                "geocode_source": "google_maps_playwright",
                "lat": g["lat"],
                "lng": g["lng"],
            })
            added += 1
        await browser.close()

    src.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
    js = "const PLACES = " + json.dumps(places, ensure_ascii=False, indent=2) + ";\n"
    (WEB / "places_data.js").write_text(js, encoding="utf-8")
    print(f"\nAdded {added}. Total: {len(places)}")


if __name__ == "__main__":
    asyncio.run(main())
