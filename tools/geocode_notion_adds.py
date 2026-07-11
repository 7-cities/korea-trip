"""Geocode curated additions from the Minjuncooks Notion vegan map, using exact KR addresses.
Also re-geocode Avec (아베끄) with its true address 애월해안로 960 (Aewol coast, not airport)."""
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
COORD_RE = re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)")
PLACE_RE = re.compile(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)")

# key -> list of fallback queries (exact Notion address first)
TARGETS = {
    "avec_fix":        ["제주 제주시 애월해안로 960", "아베끄 애월 비건"],
    "assalam":         ["제주 제주시 중앙로2길 7 아살람", "아살람 레스토랑 제주"],
    "sumbida":         ["제주 제주시 애월로 118 숨비다", "숨비다 애월"],
    "baram":           ["제주 제주시 애월읍 납읍동1길 18-14", "비건테이블바람 애월"],
    "fengohoda":       ["제주 제주시 봉성로 61 펜고호다", "펜고호다 애월"],
    "jeju_vegies":     ["제주 제주시 녹차분재로 568 제주베지스", "제주베지스 애월"],
    "dubu_hyeopjae":   ["제주 제주시 한림읍 협재10길 14", "두부 제주협재점"],
    "loving_hut":      ["제주 서귀포시 일주동로 7036 러빙헛", "러빙헛 서귀포"],
    "yuyeonhan_baker": ["제주 서귀포시 사계중앙로 48 유연한베이커", "유연한베이커 사계"],
    "ppang_sagye":     ["제주 서귀포시 향교로 151 빵사계", "빵사계 서귀포"],
    "salady_nohyeong": ["제주 제주시 연북로 24 샐러디", "샐러디 제주노형점"],
    "yuinwon":         ["제주 서귀포시 무영로254번길 17 유인원", "유인원 카페 서귀포"],
}


async def geocode(page, queries):
    for q in queries:
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
                return {"lat": float(m.group(1)), "lng": float(m.group(2)), "query": q, "slug": slug}
            await asyncio.sleep(0.4)
    return None


async def main():
    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await (await browser.new_context(locale="en-US")).new_page()
        for key, queries in TARGETS.items():
            g = await geocode(page, queries)
            results[key] = g
            if g:
                print(f"OK   {key:18s} {g['lat']:.5f},{g['lng']:.5f}  slug={g['slug']}")
            else:
                print(f"FAIL {key}")
        await browser.close()
    (HERE / "notion_adds_geocoded.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    asyncio.run(main())
