"""
Apply 2026-04-23 sheet update to places.json:
  1. Remove places no longer in the sheet (cuts)
  2. Extract new POI rows from sheet that aren't in places.json (additions)
  3. Output additions to extras_to_geocode.json for downstream Playwright geocoding
  4. Rewrite places.json minus the cuts

Final merging of geocoded additions happens in merge_additions.py.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
rows = json.loads((HERE / "sheet_hyperlinks.json").read_text(encoding="utf-8"))
places = json.loads((ROOT / "places.json").read_text(encoding="utf-8"))


def norm(s):
    return (s or "").strip().lower()


# --- Gather every string in every sheet tab for substring-match testing ---
# We need fuzzy detection because Ideas-tab entries use free-text phrases
# like "Seoul Children's Museum https://..." which won't exact-match.
MENTION_TABS = {"Naver List", "Jeju Island", "Ideas", "EventsTickets",
                "Elianas List", "Seoul", "Non-Seoul Areas"}
sheet_blob_lc = []     # list of lowercased value strings to substring-search
sheet_names_lc = set() # exact-match set for quick checks
for r in rows:
    if r["sheet"] not in MENTION_TABS:
        continue
    for v in r["values"]:
        if isinstance(v, str) and v.strip():
            s = v.strip().lower()
            sheet_names_lc.add(s)
            sheet_blob_lc.append(s)


def is_present_in_sheet(name):
    """True if `name` appears anywhere in a sheet value (exact or substring)."""
    if not name:
        return False
    nl = name.strip().lower()
    if len(nl) < 2:
        return False
    if nl in sheet_names_lc:
        return True
    # substring containment — name is contained within some cell value
    return any(nl in s for s in sheet_blob_lc)

# --- Cuts: places not mentioned in the canonical sheet tabs ---
# Only cut if BOTH name_kr and name_en are absent from sheet
kept = []
cut = []
for p in places:
    if is_present_in_sheet(p.get("name_kr")) or is_present_in_sheet(p.get("name_en")):
        kept.append(p)
    else:
        cut.append(p)

print(f"Cuts: {len(cut)} removed, {len(kept)} kept out of {len(places)}")

# --- Extract additions from Naver List ---
# Fixed Naver List layout (0-indexed):
#   col 0 = type ; col 1 = audience ; col 2 = name_kr ; col 3 = name_en_or_desc ;
#   col 4 = address ; col 5 = Google link ; col 6 = Naver link ; col 7 = extra notes
import re


def clean_en_name(s):
    """Strip parenthetical notes — 'Everland(Big Outdoor...)' -> ('Everland', 'Big Outdoor...')"""
    if not s:
        return None, None
    s = s.strip()
    m = re.match(r"^([^(]+)\s*\((.*?)\)?\s*$", s)
    if m:
        name = m.group(1).strip()
        note = m.group(2).strip().rstrip(')')
        return name, note
    return s, None


def is_dup_of_existing(name):
    """True if `name` matches an already-kept place (exact or substring)."""
    if not name:
        return False
    nl = norm(name)
    for p in kept:
        for ex in (p.get("name_kr"), p.get("name_en")):
            if not ex:
                continue
            exl = norm(ex)
            if nl == exl or nl in exl or exl in nl:
                return True
    return False


additions = []
skip_headers = {"name", "kr name", "en name", "place", "name_kr", "name_en",
                "google map links", "naver map links", "google maps", "naver maps",
                "kr", "en", "places"}

for r in rows:
    if r["sheet"] != "Naver List":
        continue
    values = r["values"]
    # Pad values so we can safely index
    values = list(values) + [None] * (8 - len(values)) if len(values) < 8 else list(values)

    # Skip blank-ish rows
    if not any(v and isinstance(v, str) and v.strip() for v in values):
        continue
    # Skip header rows
    if any(isinstance(v, str) and v.strip().lower() in skip_headers for v in values[:2]):
        continue

    # Fixed layout extraction
    ptype   = (values[0] or "").strip() if isinstance(values[0], str) else ""
    kr      = (values[2] or "").strip() if isinstance(values[2], str) else ""
    en_raw  = (values[3] or "").strip() if isinstance(values[3], str) else ""
    address = (values[4] or "").strip() if isinstance(values[4], str) else ""
    notes_extra = (values[7] or "").strip() if isinstance(values[7], str) else ""

    # Row must have a Korean name (name_kr) to be a valid POI row
    if not kr or not any('\uac00' <= c <= '\ud7a3' for c in kr):
        continue

    # Clean EN name — separate parenthetical into notes
    en, paren_note = clean_en_name(en_raw)
    notes = " / ".join(filter(None, [paren_note, notes_extra])) or None

    # If EN cell was a descriptor not a name (starts with "Mr.Han" etc.), keep it as notes
    # and fall back to using a romanization-free placeholder based on kr.
    looks_like_description = en and (
        en.startswith("Mr.") or
        " recommendation" in en_raw or
        en.lower().startswith("fortress") and "views" in en.lower()
    )
    if looks_like_description:
        notes = en_raw if not notes else f"{en_raw} / {notes}"
        en = kr  # fallback

    # Already in places.json (exact or substring match)?
    if is_dup_of_existing(kr) or (en and is_dup_of_existing(en)):
        continue
    # Already in cut list?  (don't re-add something the user removed)
    if any(norm(kr) == norm(c.get("name_kr")) or (en and norm(en) == norm(c.get("name_en"))) for c in cut):
        continue

    # Recover Naver + Google links from the row's hyperlink map
    links = r.get("links", {})
    naver_url = None
    google_url = None
    web_link = None
    for _, url in links.items():
        ul = url.lower()
        if "naver.me" in ul or "map.naver.com" in ul:
            if not naver_url:
                naver_url = url
        elif "google.com/maps" in ul:
            if not google_url:
                google_url = url
        else:
            if not web_link:
                web_link = url

    # Infer region from address
    region = "Seoul"
    if address:
        if "제주" in address:
            region = "Jeju"
        elif "부산" in address:
            region = "Busan"
        elif "강원" in address or "춘천" in address or "삼척" in address:
            region = "Gangwon"
        elif "경기" in address or "용인" in address or "과천" in address or "광주시" in address:
            region = "Gyeonggi"
        elif "인천" in address:
            region = "Incheon"
        elif "경북" in address or "경주" in address:
            region = "Gyeongsangbuk-do"
        elif "충남" in address or "공주" in address:
            region = "Chungcheongnam-do"
        elif "서울" in address:
            region = "Seoul"

    additions.append({
        "name_kr": kr or None,
        "name_en": en or None,
        "type": ptype or "Other",
        "region": region,
        "address": address or "",
        "notes": notes or "",
        "naver_url": naver_url,
        "google_url": google_url,
        "web_link": web_link,
        "source": "sheet_update_2026-04-23",
        "sheet_row": r["row"],
    })


# Dedup additions by name_en
seen = set()
unique_additions = []
for a in additions:
    key = norm(a.get("name_en")) or norm(a.get("name_kr"))
    if key in seen:
        continue
    seen.add(key)
    unique_additions.append(a)

print(f"Additions: {len(unique_additions)} new rows")

# Dump files
(HERE / "cuts.json").write_text(
    json.dumps(cut, ensure_ascii=False, indent=2), encoding="utf-8"
)
(HERE / "additions_pending.json").write_text(
    json.dumps(unique_additions, ensure_ascii=False, indent=2), encoding="utf-8"
)
# places.json gets only the kept entries; additions get merged in after geocoding
(HERE / "places_post_cut.json").write_text(
    json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8"
)

print(f"Wrote cuts.json, additions_pending.json, places_post_cut.json")
print()
print("First 5 additions:")
for a in unique_additions[:5]:
    print(f"  - {a['name_en']} ({a['name_kr']}) / {a['type']} / {a['region']}")
