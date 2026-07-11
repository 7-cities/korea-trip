"""Re-geocode + enrich the existing Cafe Hallasan entry with its real address (면수1길 48, 구좌읍)."""
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
QUERIES = ["제주 제주시 구좌읍 면수1길 48 카페한라산", "제주 제주시 구좌읍 면수1길 48", "카페한라산 구좌"]


async def geocode():
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
        return got


async def main():
    got = await geocode()
    if not got:
        print("Geocode failed")
        return
    print(f"OK {got['lat']:.5f},{got['lng']:.5f}  slug={got['slug']}")

    src = ROOT / "places.json"
    shutil.copy2(src, HERE / "places.prev.json")
    places = json.loads(src.read_text(encoding="utf-8"))
    patched = False
    for p in places:
        if p.get("name_en") == "Cafe Hallasan" and p.get("name_kr") == "카페한라산":
            p["type"] = "Coffee & Bakery"
            p["address"] = "제주시 구좌읍 면수1길 48"
            p["lat"] = got["lat"]
            p["lng"] = got["lng"]
            p["geocode_query"] = got["query"]
            p["geocode_source"] = "google_maps_playwright"
            p["notes"] = "Cafe near the Gujwa/Sehwa east coast"
            p["naver_url"] = "https://map.naver.com/p/search/카페한라산 구좌"
            patched = True
            break
    if not patched:
        print("Cafe Hallasan entry not found!")
        return
    src.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
    js = "const PLACES = " + json.dumps(places, ensure_ascii=False, indent=2) + ";\n"
    (WEB / "places_data.js").write_text(js, encoding="utf-8")
    print(f"Updated Cafe Hallasan. Total: {len(places)}")


if __name__ == "__main__":
    asyncio.run(main())
