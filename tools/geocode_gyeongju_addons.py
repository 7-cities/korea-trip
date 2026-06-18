"""Geocode 3 more Gyeongju POIs from the user's two-day agenda."""
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

TO_GEOCODE = [
    {"key": "gyerim",            "query": "경상북도 경주시 교동 1 계림"},
    {"key": "woljeonggyo",       "query": "경상북도 경주시 교동 274 월정교"},
    {"key": "gyeongju_expo_park","query": "경상북도 경주시 신평동 1095 경주엑스포대공원"},
]

COORD_RE = re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)")


async def lookup(page, url, timeout_ms=20000):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    except Exception as e:
        return None, f"goto: {e}"
    try:
        await page.wait_for_url(re.compile(r"/maps/place/"), timeout=timeout_ms)
    except Exception:
        pass
    for _ in range(15):
        m = COORD_RE.search(page.url)
        if m:
            return (float(m.group(1)), float(m.group(2))), None
        await asyncio.sleep(0.4)
    return None, "no-coord"


async def main():
    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
            locale="en-US",
        )
        page = await ctx.new_page()
        for entry in TO_GEOCODE:
            q = entry["query"]
            url = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q)
            print(f"[{entry['key']}] {q}")
            coords, err = await lookup(page, url)
            if coords:
                results[entry["key"]] = {"lat": coords[0], "lng": coords[1], "query": q}
                print(f"  OK  {coords[0]:.6f}, {coords[1]:.6f}")
            else:
                results[entry["key"]] = None
                print(f"  FAIL {err}")
        await browser.close()
    (HERE / "gyeongju_addons_geocoded.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    asyncio.run(main())
