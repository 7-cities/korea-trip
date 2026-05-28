"""
Diff freshly-exported sheet (sheet_hyperlinks.json) vs current places.json.

For each row in POI tabs:
  - take all string values as candidate names
  - if ANY candidate matches a place in places.json -> row is MATCHED
  - else -> row is a candidate ADDITION

For each place in places.json:
  - if its name_kr or name_en appears anywhere in the sheet -> still present
  - else -> candidate CUT
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


# Index places by normalized name (both KR and EN).
place_name_index = {}  # lowercase-name -> place
for p in places:
    for nm in (p.get("name_kr"), p.get("name_en")):
        if nm:
            place_name_index[norm(nm)] = p

# Tabs that contain POI rows (not free-form idea lists or config).
POI_TABS = {"Naver List", "Jeju Island", "EventsTickets", "Ideas", "Elianas List"}

# Known non-name column values — labels, categories, audience tags.
JUNK = {
    "name", "kr name", "en name", "type", "place", "link", "links", "url", "address",
    "hours", "notes", "note", "korean", "english", "category", "description",
    "google", "naver", "map", "maps", "fee", "price", "cost", "hours / closed",
    "location", "family", "kids", "kids/family", "jihyun", "eliana", "amelia",
    "michael", "food", "culture", "nature", "museum", "shopping", "activities",
    "activity", "entertainment", "restaurant", "coffee/bakery", "cafe", "café",
    "theme park", "bookstore", "music", "art class", "baking class", "cartoon cafe",
    "boardgame cafe", "cable car", "library", "accommodation",
    "craft/pearl art class", "kids museum", "game museum",
    "art shop/activities", "museum/culture", "culture/nature", "culture/food",
    "culture/activities", "culture/publication related", "culture/world heritage",
    "nature/activities", "activities/entertainment", "diy perfume",
    "book making/publishing", "classes", "-",
}


def row_candidate_names(values):
    out = []
    for v in values:
        if not v or not isinstance(v, str):
            continue
        s = v.strip()
        if len(s) < 2:
            continue
        if s.lower() in JUNK:
            continue
        if s.startswith("http") or s.startswith("=HYPERLINK") or s.startswith("="):
            continue
        out.append(s)
    return out


# --- Pass 1: classify each sheet row ---
additions = []
all_sheet_names_lc = set()

for r in rows:
    if r["sheet"] not in POI_TABS:
        continue
    names = row_candidate_names(r["values"])
    if not names:
        continue
    matched = False
    for n in names:
        nl = norm(n)
        all_sheet_names_lc.add(nl)
        if nl in place_name_index:
            matched = True
    if not matched:
        additions.append({"sheet": r["sheet"], "row": r["row"], "names": names})


# --- Pass 2: classify each place ---
cuts = []
for p in places:
    kr = norm(p.get("name_kr"))
    en = norm(p.get("name_en"))
    if (kr and kr in all_sheet_names_lc) or (en and en in all_sheet_names_lc):
        continue
    cuts.append(p)


# --- Dedup additions by their candidate-name tuple (sheet may repeat rows) ---
seen = set()
dedup_additions = []
for a in additions:
    key = (a["sheet"], tuple(a["names"]))
    if key in seen:
        continue
    seen.add(key)
    dedup_additions.append(a)

print(f"POI tabs: {sorted(POI_TABS)}")
print(f"places.json: {len(places)} entries")
print(f"Sheet rows matched to places: OK (implicit)")
print()
print(f"=== CUTS: {len(cuts)} place(s) in places.json not found in sheet ===")
for p in cuts:
    en = p.get("name_en") or ""
    kr = p.get("name_kr") or ""
    print(f"  [{p.get('region')}] {en:50s}  ({kr})  type={p.get('type')}")

print()
print(f"=== ADDITIONS: {len(dedup_additions)} sheet row(s) not in places.json ===")
for a in dedup_additions:
    print(f"  [{a['sheet']} r{a['row']}]  {a['names']}")
