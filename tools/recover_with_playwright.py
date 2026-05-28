"""
Recover failed-geocode places by driving headless Chromium against Google Maps.
Reads recovery_worklist.json, writes/updates recovery_results.json incrementally.
"""
import asyncio
import json
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).parent
WORKLIST = HERE / "recovery_worklist.json"
RESULTS = HERE / "recovery_results.json"

COORD_RE = re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)")


async def lookup(page, url, timeout_ms=12000):
    """Navigate, wait for Google Maps to redirect, return (lat, lng) or None."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    except Exception as e:
        print(f"  goto error: {e}")
        return None
    # wait for URL to morph from /search/ to /place/ (signals a single match)
    try:
        await page.wait_for_url(re.compile(r"/maps/place/"), timeout=timeout_ms)
    except Exception:
        pass  # may still have coords in /search/ URL even without /place/ redirect
    # give the @lat,lng segment a moment to settle
    for _ in range(8):
        cur = page.url
        m = COORD_RE.search(cur)
        if m:
            return float(m.group(1)), float(m.group(2))
        await asyncio.sleep(0.5)
    return None


async def main():
    worklist = json.loads(WORKLIST.read_text(encoding="utf-8"))
    results = json.loads(RESULTS.read_text(encoding="utf-8")) if RESULTS.exists() else {}

    todo = [w for w in worklist if w["name_en"] not in results]
    print(f"Total: {len(worklist)} | Already done: {len(results)} | Remaining: {len(todo)}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="en-US",
        )
        page = await context.new_page()

        for i, w in enumerate(todo, 1):
            name = w["name_en"]
            print(f"[{i}/{len(todo)}] {name[:42]:44s}", end=" ", flush=True)
            coords = await lookup(page, w["url"])
            if coords:
                results[name] = {"lat": coords[0], "lng": coords[1], "query": w["query"]}
                print(f"OK  {coords[0]:.5f}, {coords[1]:.5f}")
            else:
                results[name] = None
                print("FAIL")
            # save every 5
            if i % 5 == 0:
                RESULTS.write_text(
                    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
                )

        RESULTS.write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        await browser.close()

    ok = sum(1 for v in results.values() if v)
    print(f"\nRecovered {ok} / {len(results)} ({len(results) - ok} still failed)")


if __name__ == "__main__":
    asyncio.run(main())
