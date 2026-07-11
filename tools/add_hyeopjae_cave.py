"""Geocode + append Hyeopjae Cave (협재굴, inside Hallim Park)."""
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


async def geocode(query):
    url = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(query)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
            locale="en-US",
        )
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_url(re.compile(r"/maps/place/"), timeout=20000)
        except Exception:
            pass
        coords = None
        for _ in range(15):
            m = COORD_RE.search(page.url) or PLACE_RE.search(page.url)
            if m:
                coords = (float(m.group(1)), float(m.group(2)))
                break
            await asyncio.sleep(0.4)
        await browser.close()
        return coords


async def main():
    query = "협재굴 제주 한림공원"
    coords = await geocode(query)
    if not coords:
        print("Geocode failed")
        return
    print(f"Geocoded: {coords[0]:.6f}, {coords[1]:.6f}")

    src = ROOT / "places.json"
    shutil.copy2(src, HERE / "places.prev.json")
    places = json.loads(src.read_text(encoding="utf-8"))

    places.append({
        "type": "Nature",
        "name_kr": "협재굴",
        "name_en": "Hyeopjae Cave",
        "address": "제주특별자치도 제주시 한림읍 한림로 300 (한림공원 내)",
        "google_url": "https://www.google.com/maps/search/?api=1&query=협재굴",
        "naver_url": "https://map.naver.com/p/search/협재굴",
        "notes": "Lava tube with limestone formations — inside Hallim Park (park admission covers it); pairs with Ssangyong Cave next door",
        "region": "Jeju",
        "source": "manual_2026-06-19",
        "geocode_query": query,
        "geocode_source": "google_maps_playwright",
        "lat": coords[0],
        "lng": coords[1],
    })

    src.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
    js = "const PLACES = " + json.dumps(places, ensure_ascii=False, indent=2) + ";\n"
    (WEB / "places_data.js").write_text(js, encoding="utf-8")
    print(f"Added Hyeopjae Cave. Total: {len(places)}")


if __name__ == "__main__":
    asyncio.run(main())
