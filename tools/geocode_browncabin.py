"""Re-geocode Browncabin Pension using the specific street address."""
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
QUERIES = [
    "제주특별자치도 제주시 애월읍 소길남길 190-40",
    "190-40 소길남길 애월읍 제주시",
    "브라운캐빈 펜션 애월",
]
COORD_RE = re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)")
PLACE_RE = re.compile(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)")


async def try_query(page, q):
    url = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q)
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except Exception as e:
        return None, f"goto: {e}"
    try:
        await page.wait_for_url(re.compile(r"/maps/place/"), timeout=20000)
    except Exception:
        pass
    for _ in range(15):
        m = COORD_RE.search(page.url) or PLACE_RE.search(page.url)
        if m:
            return (float(m.group(1)), float(m.group(2))), page.url
        await asyncio.sleep(0.4)
    return None, page.url


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
            locale="en-US",
        )
        page = await ctx.new_page()
        for q in QUERIES:
            print(f"try: {q}")
            coords, url = await try_query(page, q)
            if coords:
                print(f"  OK  {coords[0]:.6f}, {coords[1]:.6f}")
                (HERE / "browncabin_geocoded.json").write_text(
                    json.dumps({"lat": coords[0], "lng": coords[1], "query": q,
                                "url": url}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                await browser.close()
                return
            else:
                print(f"  no coords; url: {url[:120]}")
        print("All queries failed")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
