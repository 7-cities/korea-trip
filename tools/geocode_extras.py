"""Geocode entries from extras_to_geocode.json via Playwright + Google Maps."""
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
EXTRAS = HERE / "extras_to_geocode.json"
RESULTS = HERE / "extras_geocoded.json"

COORD_RE = re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)")


def build_query(p):
    """For entries without addresses, search by name + region hint."""
    parts = []
    if p.get("name_kr"):
        parts.append(p["name_kr"])
    elif p.get("name_en"):
        parts.append(p["name_en"])
    # add a context hint
    region = p.get("region") or ""
    notes = p.get("notes") or ""
    if region == "Jeju" or "제주" in notes:
        parts.append("제주")
    else:
        parts.append("서울")
    return " ".join(parts)


async def lookup(page, url, timeout_ms=12000):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    except Exception as e:
        print(f"  goto error: {e}")
        return None
    try:
        await page.wait_for_url(re.compile(r"/maps/place/"), timeout=timeout_ms)
    except Exception:
        pass
    for _ in range(8):
        m = COORD_RE.search(page.url)
        if m:
            return float(m.group(1)), float(m.group(2))
        await asyncio.sleep(0.5)
    return None


async def main():
    extras = json.loads(EXTRAS.read_text(encoding="utf-8"))
    results = json.loads(RESULTS.read_text(encoding="utf-8")) if RESULTS.exists() else {}

    todo = [p for p in extras if p["name_en"] not in results]
    print(f"Total: {len(extras)} | Done: {len(results)} | Remaining: {len(todo)}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="en-US",
        )
        page = await context.new_page()
        for i, place in enumerate(todo, 1):
            q = build_query(place)
            url = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q)
            name = place["name_en"]
            print(f"[{i}/{len(todo)}] {name[:42]:44s}", end=" ", flush=True)
            coords = await lookup(page, url)
            if coords:
                results[name] = {"lat": coords[0], "lng": coords[1], "query": q}
                print(f"OK  {coords[0]:.5f}, {coords[1]:.5f}")
            else:
                results[name] = None
                print("FAIL")
            if i % 5 == 0:
                RESULTS.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        RESULTS.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        await browser.close()
    ok = sum(1 for v in results.values() if v)
    print(f"\nGeocoded {ok} / {len(results)}")


if __name__ == "__main__":
    asyncio.run(main())
