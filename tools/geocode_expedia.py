"""Geocode Expedia Group Korea office (Tower 8, Jongno-gu)."""
import asyncio
import json
import re
import sys
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).parent
QUERY = "서울특별시 종로구 종로5길 7 타워8"
COORD_RE = re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)")


async def main():
    url = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(QUERY)
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
        except Exception as e:
            print(f"goto failed: {e}")
            return
        try:
            await page.wait_for_url(re.compile(r"/maps/place/"), timeout=20000)
        except Exception:
            pass
        coords = None
        for _ in range(15):
            m = COORD_RE.search(page.url)
            if m:
                coords = (float(m.group(1)), float(m.group(2)))
                break
            await asyncio.sleep(0.4)
        if coords:
            print(f"OK  {coords[0]:.6f}, {coords[1]:.6f}")
            (HERE / "expedia_geocoded.json").write_text(
                json.dumps({"lat": coords[0], "lng": coords[1], "query": QUERY},
                           ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        else:
            print(f"FAIL no-coord; final url: {page.url}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
