"""Check which hand-drawn-map POIs exist in places.json (Jeju region only)."""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
places = json.loads((ROOT / "places.json").read_text(encoding="utf-8"))

wanted = {
    "Arte Museum": ["arte", "아르떼"],
    "Hyeopjae Beach": ["hyeopjae beach", "협재 해수욕장", "협재해수욕장"],
    "Hyeopjae Cave": ["hyeopjae cave", "협재굴"],
    "Volcanic Cone / Saebyeol Oreum (sunset hike)": ["saebyeol", "새별오름"],
    "Jeju's Lava Forest": ["lava", "곶자왈", "gotjawal"],
    "Camellia Hill": ["camellia", "카멜리아"],
    "Jeju Fairytale Village": ["fairytale", "동화마을", "fairy"],
    "Yongnuni/Yangnuni Oreum": ["yongnuni", "yangnuni", "용눈이"],
    "Bonte Museum": ["bonte", "bonté", "본태"],
    "Cheonjeyeon Falls": ["cheonjeyeon", "천제연"],
    "Lee Jung Seop Art Museum": ["jung seop", "jungseop", "이중섭"],
    "Jusangjeolli Cliff": ["jusangjeolli", "주상절리"],
    "Jeju Haenyeo Museum": ["haenyeo", "해녀박물관"],
    "Bijarim Forest": ["bijarim", "비자림"],
    "Seongsan Sunrise Peak": ["sunrise peak", "seongsan", "성산일출봉", "성산 일출봉"],
    "Aqua Planet / Aquarium": ["aqua", "아쿠아플라넷", "aquarium"],
    "Jeju Folk Village": ["folk village", "민속촌"],
}


def find(needles):
    hits = []
    for p in places:
        if p.get("region") != "Jeju":
            continue
        blob = " ".join(str(p.get(k) or "") for k in ("name_en", "name_kr", "type", "address")).lower()
        if any(n.lower() in blob for n in needles):
            hits.append(p.get("name_en") or p.get("name_kr"))
    return hits


missing = []
for label, needles in wanted.items():
    hits = find(needles)
    status = "PRESENT" if hits else "MISSING"
    if not hits:
        missing.append(label)
    print(f"[{status:7s}] {label}")
    for h in hits:
        print(f"            -> {h}")

print("\nMISSING:", len(missing))
for m in missing:
    print(" -", m)
