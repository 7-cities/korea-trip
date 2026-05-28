"""Geocode the 22 pending additions via Playwright + Google Maps."""
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
PENDING = HERE / "additions_pending.json"
RESULTS = HERE / "additions_geocoded.json"

COORD_RE = re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)")


def build_query(a):
    """Prefer KR address (most specific), fall back to KR name + city hint."""
    if a.get("address"):
        return a["address"]
    parts = []
    if a.get("name_kr"):
        parts.append(a["name_kr"])
    elif a.get("name_en"):
        parts.append(a["name_en"])
    region = a.get("region") or ""
    hint_map = {
        "Seoul": "서울", "Jeju": "제주", "Busan": "부산", "Gangwon": "강원",
        "Gyeonggi": "경기", "Incheon": "인천",
        "Gyeongsangbuk-do": "경북", "Chungcheongnam-do": "충남",
    }
    if region in hint_map:
        parts.append(hint_map[region])
    return " ".join(parts)


async def lookup(page, url, timeout_ms=15000):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    except Exception as e:
        return None, f"goto: {e}"
    try:
        await page.wait_for_url(re.compile(r"/maps/place/"), timeout=timeout_ms)
    except Exception:
        pass
    for _ in range(10):
        m = COORD_RE.search(page.url)
        if m:
            return (float(m.group(1)), float(m.group(2))), None
        await asyncio.sleep(0.4)
    return None, "no-coord"


async def main():
    pending = json.loads(PENDING.read_text(encoding="utf-8"))
    results = json.loads(RESULTS.read_text(encoding="utf-8")) if RESULTS.exists() else {}

    todo = [a for a in pending if a["name_en"] not in results]
    print(f"Pending: {len(pending)} | Done: {len(results)} | Remaining: {len(todo)}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
            locale="en-US",
        )
        page = await context.new_page()
        for i, a in enumerate(todo, 1):
            q = build_query(a)
            url = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q)
            name = a["name_en"]
            print(f"[{i}/{len(todo)}] {name[:48]:50s}", end=" ", flush=True)
            coords, err = await lookup(page, url)
            if coords:
                results[name] = {"lat": coords[0], "lng": coords[1], "query": q}
                print(f"OK  {coords[0]:.5f}, {coords[1]:.5f}")
            else:
                results[name] = None
                print(f"FAIL ({err})")
            if i % 5 == 0:
                RESULTS.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        RESULTS.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        await browser.close()
    ok = sum(1 for v in results.values() if v)
    print(f"\nGeocoded {ok} / {len(results)}")


if __name__ == "__main__":
    asyncio.run(main())
