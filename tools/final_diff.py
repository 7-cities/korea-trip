"""
Comprehensive diff with proper handling:
  - Check ALL sheet rows in Naver List, Jeju Island, EventsTickets for POI structure
  - Match against existing places by name_kr OR name_en (exact + substring both ways)
  - Report:
      EXISTS  = found a match (no action)
      RENAME  = match via substring (existing should be UPDATED to new sheet entry)
      NEW     = no match anywhere (ADD)
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
rows = json.loads((HERE / "sheet_hyperlinks.json").read_text(encoding="utf-8"))
places = json.loads((ROOT / "places.json").read_text(encoding="utf-8"))


def norm(s):
    return (s or "").strip().lower()


def find_existing(kr, en):
    nkr, nen = norm(kr), norm(en)
    for p in places:
        pkr, pen = norm(p.get("name_kr")), norm(p.get("name_en"))
        if (nkr and pkr == nkr) or (nen and pen == nen):
            return p, "EXACT"
    for p in places:
        pkr, pen = norm(p.get("name_kr")), norm(p.get("name_en"))
        if nkr and pkr and (nkr in pkr or pkr in nkr):
            return p, f"SUBSTR-KR({p.get('name_kr')})"
        if nen and pen and len(nen) >= 4 and len(pen) >= 4 and (nen in pen or pen in nen):
            return p, f"SUBSTR-EN({p.get('name_en')})"
    return None, None


def clean_en(s):
    """Strip parenthetical -> name, note."""
    if not s:
        return None, None
    s = s.strip()
    m = re.match(r"^([^(]+?)\s*\((.*?)\)?\s*$", s)
    if m:
        return m.group(1).strip(), m.group(2).rstrip(")").strip()
    return s, None


def infer_region(addr):
    if not addr:
        return "Seoul"
    a = addr
    if "제주" in a: return "Jeju"
    if "부산" in a: return "Busan"
    if "강원" in a or "춘천" in a or "삼척" in a: return "Gangwon"
    if "경기" in a or "용인" in a or "과천" in a or "수원" in a or "양주" in a or "파주" in a: return "Gyeonggi"
    if "인천" in a: return "Incheon"
    if "경북" in a or "경주" in a: return "Gyeongsangbuk-do"
    if "충남" in a or "공주" in a or "부여" in a: return "Chungcheongnam-do"
    if "대전" in a: return "Daejeon"
    if "광주광역" in a: return "Gwangju"
    return "Seoul"


# Look at all POI-table rows
TABS_POI = {"Naver List", "Jeju Island", "EventsTickets"}

new_pois = []
renames = []
exists_count = 0
for r in rows:
    if r["sheet"] not in TABS_POI:
        continue
    vals = list(r["values"]) + [None] * max(0, 9 - len(r["values"]))
    # POI rows must have a KR name (col 2) with Hangul
    kr_raw = vals[2] if isinstance(vals[2], str) else None
    if not kr_raw or not any('가' <= c <= '힣' for c in kr_raw):
        continue
    kr = kr_raw.strip()
    en_raw = (vals[3] or "").strip() if isinstance(vals[3], str) else ""
    en, paren_note = clean_en(en_raw)
    ptype = (vals[0] or "").strip() if isinstance(vals[0], str) else "Other"
    addr = (vals[4] or "").strip() if isinstance(vals[4], str) else ""
    notes_extra = (vals[7] or "").strip() if isinstance(vals[7], str) else ""

    match, why = find_existing(kr, en)
    if match and why == "EXACT":
        exists_count += 1
        continue

    # Resolve links
    links = r.get("links", {})
    naver_url = google_url = web_link = None
    for _, url in links.items():
        ul = url.lower()
        if ("naver.me" in ul or "map.naver.com" in ul) and not naver_url:
            naver_url = url
        elif "google.com/maps" in ul and not google_url:
            google_url = url
        elif not web_link:
            web_link = url

    notes = " / ".join(filter(None, [paren_note, notes_extra])) or ""
    entry = {
        "sheet_row": r["row"],
        "sheet_tab": r["sheet"],
        "type": ptype or "Other",
        "name_kr": kr,
        "name_en": en,
        "address": addr,
        "notes": notes,
        "region": infer_region(addr),
        "naver_url": naver_url,
        "google_url": google_url,
        "web_link": web_link,
    }
    if match:
        renames.append((entry, match, why))
    else:
        new_pois.append(entry)


# Print findings
print(f"EXACT matches: {exists_count}")
print()
print(f"=== RENAMES ({len(renames)}) — existing entries that match by substring ===")
for e, m, why in renames:
    print(f"  [{e['sheet_tab']} r{e['sheet_row']}]  {e['name_kr']} / {e['name_en']}")
    print(f"      via {why}")
    print(f"      existing KR={m.get('name_kr')!r}  EN={m.get('name_en')!r}")
    print()

print(f"=== NEW POIs ({len(new_pois)}) — no match in places.json ===")
for e in new_pois:
    print(f"  [{e['sheet_tab']} r{e['sheet_row']}]  [{e['type']}]  {e['name_kr']} / {e['name_en']}")
    print(f"      addr: {e['address']}")
    if e["naver_url"]: print(f"      naver: {e['naver_url']}")
    print()

# Also check for STRICT cuts: places.json entries that don't appear in sheet at all
print("=" * 60)
print("Checking for STRICT cuts (existing places not in sheet anywhere)")
print("=" * 60)
all_text = []
for r in rows:
    for v in r["values"]:
        if isinstance(v, str):
            all_text.append(v)
blob = "\n".join(all_text).lower()
real_cuts = []
for p in places:
    kr = norm(p.get("name_kr"))
    en = norm(p.get("name_en"))
    found = False
    if kr and len(kr) >= 2 and kr in blob:
        found = True
    if en and len(en) >= 3 and en in blob:
        found = True
    if not found:
        real_cuts.append(p)
print(f"\nTrue cuts: {len(real_cuts)}")
for p in real_cuts:
    print(f"  [{p.get('region')}] {p.get('name_kr')} / {p.get('name_en')} ({p.get('type')})")

# Save the new POI candidates as additions_pending.json for downstream geocoding
(HERE / "additions_pending_v2.json").write_text(
    json.dumps([{**e, "source": "sheet_update_2026-05-27"} for e in new_pois],
               ensure_ascii=False, indent=2),
    encoding="utf-8",
)
(HERE / "renames_v2.json").write_text(
    json.dumps([{"new": e, "existing_name_kr": m.get("name_kr"),
                 "existing_name_en": m.get("name_en"), "match_reason": why}
                for e, m, why in renames],
               ensure_ascii=False, indent=2),
    encoding="utf-8",
)
(HERE / "real_cuts_v2.json").write_text(
    json.dumps(real_cuts, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(f"\nWrote additions_pending_v2.json, renames_v2.json, real_cuts_v2.json")
