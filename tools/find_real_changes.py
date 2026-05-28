"""Find genuinely-new Naver List rows (high row numbers) and report what we have/don't have."""
import json
from pathlib import Path

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
rows = json.loads((HERE / "sheet_hyperlinks.json").read_text(encoding="utf-8"))
places = json.loads((ROOT / "places.json").read_text(encoding="utf-8"))


def norm(s):
    return (s or "").strip().lower()


existing_kr = {norm(p.get("name_kr")) for p in places if p.get("name_kr")}
existing_en = {norm(p.get("name_en")) for p in places if p.get("name_en")}


def find_existing(kr, en):
    """Return existing place that matches kr/en exactly or via substring, else None."""
    nkr = norm(kr)
    nen = norm(en)
    # 1: exact match
    for p in places:
        pkr = norm(p.get("name_kr"))
        pen = norm(p.get("name_en"))
        if (nkr and pkr == nkr) or (nen and pen == nen):
            return p, "EXACT"
    # 2: substring match
    for p in places:
        pkr = norm(p.get("name_kr"))
        pen = norm(p.get("name_en"))
        if nkr and pkr:
            if nkr in pkr or pkr in nkr:
                return p, f"SUBSTR-KR ({pkr!r})"
        if nen and pen:
            if nen in pen or pen in nen:
                return p, f"SUBSTR-EN ({pen!r})"
    return None, None


print("Latest Naver List entries (row >= 700):\n")
for r in rows:
    if r["sheet"] != "Naver List":
        continue
    if r["row"] < 700:
        continue
    values = list(r["values"]) + [None] * max(0, 8 - len(r["values"]))
    if not any(v and isinstance(v, str) and v.strip() for v in values):
        continue
    kr = (values[2] or "").strip() if isinstance(values[2], str) else ""
    en = (values[3] or "").strip() if isinstance(values[3], str) else ""
    ptype = (values[0] or "").strip() if isinstance(values[0], str) else ""
    if not kr or not any('가' <= c <= '힣' for c in kr):
        continue
    match, why = find_existing(kr, en)
    status = "EXISTS" if match else "NEW   "
    if match and "SUBSTR" in why:
        status = "RENAME?"
    print(f"r{r['row']:3d}  {status}  [{ptype}]  {kr}  /  {en}")
    if match and "SUBSTR" in why:
        print(f"       → matches existing: {match.get('name_kr')!r} / {match.get('name_en')!r}  via {why}")

print()
print("=" * 60)
print("All Naver List rows — show NEW only")
print("=" * 60)
new_count = 0
for r in rows:
    if r["sheet"] != "Naver List":
        continue
    values = list(r["values"]) + [None] * max(0, 8 - len(r["values"]))
    if not any(v and isinstance(v, str) and v.strip() for v in values):
        continue
    kr = (values[2] or "").strip() if isinstance(values[2], str) else ""
    en = (values[3] or "").strip() if isinstance(values[3], str) else ""
    ptype = (values[0] or "").strip() if isinstance(values[0], str) else ""
    if not kr or not any('가' <= c <= '힣' for c in kr):
        continue
    match, why = find_existing(kr, en)
    if not match:
        new_count += 1
        addr = (values[4] or "").strip() if isinstance(values[4], str) else ""
        print(f"r{r['row']:3d}  [{ptype}]  KR={kr}  EN={en}")
        print(f"      addr: {addr}")
print(f"\nTotal NEW (no match) in Naver List: {new_count}")
