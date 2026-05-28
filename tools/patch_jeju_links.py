"""Apply WebSearch-derived web_links to remaining Jeju places."""
import json
from pathlib import Path

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
places = json.loads((ROOT / "places.json").read_text(encoding="utf-8"))

JEJU_LINKS = {
    "Hallim Park": "https://english.visitkorea.or.kr/svc/whereToGo/locIntrdn/rgnContentsView.do?vcontsId=104761",
    "Little Prince Museum": "https://www.lepetitprince.com/en/events-around-the-world/the-little-prince-museum-opens-in-jeju-island/",
    "Teddy Bear Museum": "http://www.teddybearmuseum.com/",
    "Lee Jung-seop Art Museum": "https://english.visitkorea.or.kr/svc/contents/contentsView.do?vcontsId=90770",
    "Aqua Planet Jeju": "https://m.aquaplanet.co.kr/eng/jeju/index.do",
    "Innisfree Jeju House": "https://english.visitkorea.or.kr/svc/whereToGo/locIntrdn/rgnContentsView.do?vcontsId=65961",
    "Cafe Hallasan": "https://cafe-hallasan.goto-where.com/",
    "Jeju Glass Museum": "https://english.visitkorea.or.kr/svc/whereToGo/locIntrdn/rgnContentsView.do?vcontsId=80259",
    "Benggwidi Cave": "https://whc.unesco.org/en/list/1264/",  # UNESCO Jeju lava tube system
    "Drukumda Jeju Seongsan Branch": "https://m.visitjeju.net/en/detail/view?contentsid=CNTS_000000000020985",
    "Citrus Museum Experience Center": "https://english.visitkorea.or.kr/svc/contents/contentsView.do?vcontsId=78516",
    "Nohyung Supermarket": "http://nohyung-supermarket.com/",
    # No authoritative URL found:
    #   "Book & Toy Museum"
    #   "Nangman Haenyeo Souvenir Shop"
    #   "Dal Cheese Gujwa Sehwa Branch"
}

added = 0
for p in places:
    if p.get("web_link"):
        continue
    url = JEJU_LINKS.get(p["name_en"])
    if url:
        p["web_link"] = url
        added += 1

print(f"+web_link (Jeju): {added}")
jeju = [p for p in places if p.get("region") == "Jeju"]
print(f"Jeju: {len(jeju)} total, {sum(1 for p in jeju if p.get('web_link'))} with web_link")

(ROOT / "places.json").write_text(
    json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8"
)
js = "const PLACES = " + json.dumps(places, ensure_ascii=False, indent=2) + ";\n"
(WEB / "places_data.js").write_text(js, encoding="utf-8")
print("places.json + places_data.js rewritten")
