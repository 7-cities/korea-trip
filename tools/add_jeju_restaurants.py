"""Geocode + append the 10 diet-safe Jeju restaurants (vegan spots + hairtail houses).

Each entry carries fallback queries — first geocode hit wins. Results logged with the
final Google Maps URL so a bad match is visible in the output.
"""
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

RESTAURANTS = [
    {
        "name_kr": "앤드유 카페", "name_en": "And Yu Cafe (vegan)",
        "queries": ["제주시 한림읍 한림로 518 앤드유", "And Yu Cafe Hallim Jeju"],
        "address": "제주특별자치도 제주시 한림읍 한림로 518",
        "notes": "All-vegan (safe: no pork/shellfish/meat+milk). Bean burgers, 'chicken' nuggets, chickpea curry, cakes. Closed Tue-Wed; 12-3 / 5-9 — call ahead. ~20 min from Browncabin, pairs with Hyeopjae Beach",
    },
    {
        "name_kr": "다소니", "name_en": "Dasoni (temple food)",
        "queries": ["다소니 제주 사찰음식", "Dasoni vegan Jeju"],
        "address": "제주시 (한옥 사찰음식)",
        "notes": "All-vegan temple food in a hanok — lotus rice, perilla sujebi, bibimbap. The 'nice dinner' pick when in Jeju City",
    },
    {
        "name_kr": "칠분의 오", "name_en": "Five Seventh (vegan)",
        "queries": ["칠분의오 제주 비건", "Five Seventh vegan Jeju"],
        "address": "제주시 (북부)",
        "notes": "All-vegan — vegan chicken (dudumchic), tteokbokki, pasta, burgers, cakes. Fri-Tue 12-7, Wed 12-4",
    },
    {
        "name_kr": "란스키친", "name_en": "Lan's Kitchen (vegan)",
        "queries": ["란스키친 제주 비건", "Lan's Kitchen vegan Jeju"],
        "address": "제주시 (북부)",
        "notes": "All-vegan Korean + Vietnamese, friendly owner",
    },
    {
        "name_kr": "아베크 제주", "name_en": "Avec (vegan)",
        "queries": ["아베크 제주 비건 식당", "Avec vegan restaurant Jeju airport"],
        "address": "제주시 (공항 근처)",
        "notes": "All-vegan Western — open sandwiches, bean burgers, pastas (~$13/dish). Near the airport, good first/last-day stop",
    },
    {
        "name_kr": "라즈마할", "name_en": "Rajmahal Indian Restaurant",
        "queries": ["라즈마할 제주", "Rajmahal Indian Jeju"],
        "address": "제주시",
        "notes": "Indian — chana masala, dahl, veg biryani; vegan on request. CAUTION: ask about peanut/cashew in curries. Daily 11:30-23:00",
    },
    {
        "name_kr": "타코맛심", "name_en": "Taco Massim",
        "queries": ["타코맛심 제주 구좌", "Taco Massim Gujwa Jeju"],
        "address": "제주시 구좌읍",
        "notes": "Mexican with vegan options, English-speaking owner. Daily 12-8. East side — only if doing an east-island day",
    },
    {
        "name_kr": "제주광해 애월", "name_en": "Jeju Gwanghae (hairtail)",
        "queries": ["제주광해 애월해안로 867", "제주광해 애월 갈치"],
        "address": "제주시 애월읍 애월해안로 867",
        "notes": "Grilled + braised hairtail (fin fish — safe), ocean-view seating on the Aewol coastal road. Daily 10-20. Ask 조개류·새우 빼주세요 for braises; skip kimchi (shrimp jeotgal)",
    },
    {
        "name_kr": "갈치바다", "name_en": "Galchi Bada (hairtail)",
        "queries": ["갈치바다 애월읍 애월로", "갈치바다 애월 갈치구이"],
        "address": "제주시 애월읍 애월로 15-1",
        "notes": "Whole grilled hairtail with bones removed — best with kids. Mild braise. Daily 10-21, parking, reservations. Same shellfish/banchan cautions",
    },
    {
        "name_kr": "애월 갈치 암행어사", "name_en": "Galchi Amhaengeosa (hairtail)",
        "queries": ["애월 갈치 암행어사", "갈치 암행어사 애월"],
        "address": "제주시 애월읍",
        "notes": "Whole braised hairtail specialist. Year-round 11-21:30. Same shellfish/banchan cautions",
    },
]


async def geocode(page, query):
    url = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(query)
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except Exception:
        return None, None
    try:
        await page.wait_for_url(re.compile(r"/maps/place/"), timeout=15000)
    except Exception:
        pass
    for _ in range(12):
        m = COORD_RE.search(page.url) or PLACE_RE.search(page.url)
        if m:
            return (float(m.group(1)), float(m.group(2))), page.url
        await asyncio.sleep(0.4)
    return None, page.url


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
        for r in RESTAURANTS:
            got = None
            for q in r["queries"]:
                coords, final_url = await geocode(page, q)
                if coords:
                    got = {"lat": coords[0], "lng": coords[1], "query": q}
                    print(f"OK   {r['name_en']:38s} {coords[0]:.5f},{coords[1]:.5f}  via {q!r}")
                    # Show place slug from URL for sanity-check
                    mm = re.search(r"/maps/place/([^/]+)/", final_url or "")
                    if mm:
                        print(f"     matched: {urllib.parse.unquote(mm.group(1))[:70]}")
                    break
            if not got:
                print(f"FAIL {r['name_en']}")
            results[r["name_en"]] = got
        await browser.close()

    (HERE / "jeju_restaurants_geocoded.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\nWrote jeju_restaurants_geocoded.json — review matches, then run merge step")


if __name__ == "__main__":
    asyncio.run(main())
