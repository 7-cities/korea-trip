"""Debug apply_sheet_changes — print why each Naver List addition was rejected."""
import json
from pathlib import Path

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
rows = json.loads((HERE / "sheet_hyperlinks.json").read_text(encoding="utf-8"))
places = json.loads((ROOT / "places.json").read_text(encoding="utf-8"))


def norm(s):
    return (s or "").strip().lower()


# Build sheet blob (same as apply_sheet_changes)
MENTION_TABS = {"Naver List", "Jeju Island", "Ideas", "EventsTickets",
                "Elianas List", "Seoul", "Non-Seoul Areas"}
sheet_names_lc = set()
sheet_blob_lc = []
for r in rows:
    if r["sheet"] not in MENTION_TABS:
        continue
    for v in r["values"]:
        if isinstance(v, str) and v.strip():
            s = v.strip().lower()
            sheet_names_lc.add(s)
            sheet_blob_lc.append(s)


def is_present_in_sheet(name):
    if not name:
        return False
    nl = name.strip().lower()
    if len(nl) < 2:
        return False
    if nl in sheet_names_lc:
        return True
    return any(nl in s for s in sheet_blob_lc)


# Decide kept vs cut
kept = [p for p in places if is_present_in_sheet(p.get("name_kr")) or is_present_in_sheet(p.get("name_en"))]
cut = [p for p in places if p not in kept]


def is_dup_of_existing(name):
    if not name:
        return None
    nl = norm(name)
    for p in kept:
        for ex in (p.get("name_kr"), p.get("name_en")):
            if not ex:
                continue
            exl = norm(ex)
            if nl == exl:
                return f"EXACT {ex!r}"
            if nl in exl:
                return f"new IN existing {ex!r}"
            if exl in nl:
                return f"existing IN new {ex!r}"
    return None


skip_headers = {"name", "kr name", "en name", "place", "name_kr", "name_en",
                "google map links", "naver map links", "google maps", "naver maps",
                "kr", "en", "places"}

for r in rows:
    if r["sheet"] != "Naver List":
        continue
    values = list(r["values"]) + [None] * max(0, 8 - len(r["values"]))
    if not any(v and isinstance(v, str) and v.strip() for v in values):
        continue
    if any(isinstance(v, str) and v.strip().lower() in skip_headers for v in values[:2]):
        continue

    kr = (values[2] or "").strip() if isinstance(values[2], str) else ""
    en = (values[3] or "").strip() if isinstance(values[3], str) else ""
    if not kr or not any('가' <= c <= '힣' for c in kr):
        continue

    kr_dup = is_dup_of_existing(kr)
    en_dup = is_dup_of_existing(en) if en else None
    if not (kr_dup or en_dup):
        print(f"row {r['row']:4d}  NEW  KR={kr!r}  EN={en!r}")
    elif kr_dup and en_dup and "EXACT" in kr_dup:
        pass  # silent — clear exact dup
    else:
        print(f"row {r['row']:4d}  AMBIG  KR={kr!r}  EN={en!r}")
        if kr_dup: print(f"    kr_dup: {kr_dup}")
        if en_dup: print(f"    en_dup: {en_dup}")
