"""Geocode + append 달치즈 구좌세화점 (Dalcheese Sehwa) cafe."""
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
QUERIES = ["제주 제주시 구좌읍 해녀박물관길 35 달치즈", "달치즈 구좌세화점", "제주 구좌읍 세화리 1476-12"]


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await (await browser.new_context(locale="en-US")).new_page()
        got = None
        for q in QUERIES:
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
                    slug = urllib.parse.unquote(mm.group(1))[:50] if mm else "?"
                    got = {"lat": float(m.group(1)), "lng": float(m.group(2)), "query": q, "slug": slug}
                    break
                await asyncio.sleep(0.4)
            if got:
                break
        await browser.close()

    if not got:
        print("Geocode failed")
        return
    print(f"OK {got['lat']:.5f},{got['lng']:.5f}  slug={got['slug']}")

    src = ROOT / "places.json"
    shutil.copy2(src, HERE / "places.prev.json")
    places = json.loads(src.read_text(encoding="utf-8"))
    places.append({
        "type": "Coffee & Bakery",
        "name_kr": "달치즈 구좌세화점",
        "name_en": "Dalcheese Sehwa",
        "address": "제주시 구좌읍 해녀박물관길 35 (세화리 1476-12)",
        "google_url": "https://www.google.com/maps/search/?api=1&query=달치즈+구좌세화점",
        "naver_url": "https://naver.me/FEgnqPK7",
        "notes": "Cheese cafe near Haenyeo Museum, Sehwa (east coast). Dairy-forward — fine on the no-meat+milk rule as long as not paired with meat",
        "region": "Jeju",
        "source": "manual_2026-06-19",
        "geocode_query": got["query"],
        "geocode_source": "google_maps_playwright",
        "lat": got["lat"],
        "lng": got["lng"],
    })
    src.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
    js = "const PLACES = " + json.dumps(places, ensure_ascii=False, indent=2) + ";\n"
    (WEB / "places_data.js").write_text(js, encoding="utf-8")
    print(f"Added Dalcheese Sehwa. Total: {len(places)}")


if __name__ == "__main__":
    asyncio.run(main())
