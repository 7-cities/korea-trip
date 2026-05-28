"""
1. Add web_link to extras_keepers (where we found one via WebSearch).
2. Merge keepers into places.json -> regenerate places_data.js.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
keepers = json.loads((HERE / "extras_keepers.json").read_text(encoding="utf-8"))
places = json.loads((ROOT / "places.json").read_text(encoding="utf-8"))

# WebSearch-derived info URLs.  Preference: english.visitseoul.net > visitkorea > official site > wikipedia.
# Keys are name_en exactly as in extras_keepers.json.
LINKS = {
    "Haneul Park": "https://english.visitseoul.net/nature/Haneul-Park_/3831",
    "Seoul Forest": "https://english.visitseoul.net/nature/Seoul-Forest/ENP001838",
    "Seokchon Lake": "https://english.visitseoul.net/nature/seokchon-lake-park_/1783",
    "Cheonggyecheon stream": "https://english.visitseoul.net/area/CheonggyecheonStream/ENP000034",
    "Gyeongbokgung Palace changing of the guard": "https://english.visitseoul.net/events/Changing-of-the-Royal-Guard-at-Gyeongbokgung-Palace-en/ENP008256",
    "Seoul Children's Museum": "https://www.seoulchildrensmuseum.org/eng/",
    "Samcheong-dong": "https://english.visitseoul.net/attractions/samcheong-dong_/2124",
    "Bukhansan National Park": "https://english.knps.or.kr/Knp/Bukhansan/Intro/Introduction.aspx",
    "Itaewon": "https://english.visitseoul.net/attractions/Itaewon-Special-Tourist-Zone/ENP001066",
    "Yongsan Park": "https://en.wikipedia.org/wiki/Yongsan_Family_Park",
    "Dongdaemun design center": "https://www.ddp.or.kr/?menuno=346",
    "Lotte World Mall": "https://www.lwt.co.kr/en/",
    "Play in Museum": "https://www.koreaherald.com/article/1443877",
    "Seoul National Arts Center": "https://english.visitseoul.net/gangnamarea/Seoul-Arts-Center/ENP003986",
    "Seoul Grand Park (zoo and botanical garden)": "https://english.visitseoul.net/nature/Seoul-Grand-Park/ENP005475",
    "아트박스(stationary store)": "https://en.wikipedia.org/wiki/Artbox",
    # 한국전통자수 작품 — no authoritative link found for the specific Gwangjang Market workshop; leave unset
    "미미라인 명동점 7번출구 (Mimiline/Shopping)": "https://mimi-line.co.kr/",
    "국립민속박물관 추억의 거리(레트로 거리 재현)안국역 1번 출구": "https://www.nfm.go.kr/",
    "Artbox Sinchon": "https://english.visitkorea.or.kr/svc/contents/contentsView.do?vcontsId=91923",
    "Animate Hongdae": "https://www.animate.co.jp/en/shop/hongdae/",
    "Kyobo Book Centre Gwanghamun": "https://english.visitseoul.net/entertainment/Kyobo-Bookstore-Gwanghwamun-Branch/ENP040172",
}

added = 0
already = 0
for p in keepers:
    if p.get("web_link"):
        already += 1
        continue
    url = LINKS.get(p["name_en"])
    if url:
        p["web_link"] = url
        added += 1

print(f"web_link: +{added} added, {already} already had one (from sheet)")
no_link = [p["name_en"] for p in keepers if not p.get("web_link")]
print(f"  without link: {len(no_link)} -> {no_link}")

# Save annotated keepers (audit trail)
(HERE / "extras_keepers.json").write_text(
    json.dumps(keepers, ensure_ascii=False, indent=2), encoding="utf-8"
)

# Merge into places.json
merged = places + keepers
(ROOT / "places.json").write_text(
    json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
)
js = "const PLACES = " + json.dumps(merged, ensure_ascii=False, indent=2) + ";\n"
(WEB / "places_data.js").write_text(js, encoding="utf-8")

print(f"places.json:    {len(merged)} (was {len(places)}, +{len(keepers)})")
print(f"places_data.js: {len(merged)} entries written")
