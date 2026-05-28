"""
Parses the Korea trip planning sheet (markdown) into structured JSON,
then geocodes each place via Nominatim (OpenStreetMap, free).

Usage: python parse_and_geocode.py
Output: places.json (with lat/lng) and places_failed.json (anything we couldn't geocode)
"""
import json
import re
import sys
import time
from pathlib import Path
import urllib.parse
import urllib.request

# Windows console defaults to cp1252 — force UTF-8 so Korean prints don't crash.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
SHEET_PATH = HERE / "sheet_raw.md"
OUT_PATH = ROOT / "places.json"
FAILED_PATH = HERE / "places_failed.json"
CACHE_PATH = HERE / "geocode_cache.json"

NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "korea-trip-2026-personal-planning/1.0 (michael.e.tarr@gmail.com)"


def parse_main_places(sheet_text):
    """Parse the big 'Type | KR | EN | Address | Google | Naver | Notes' table."""
    places = []
    # find tables that have the 7-column header
    lines = sheet_text.split("\n")
    in_table = False
    for line in lines:
        line = line.strip()
        if line.startswith("| Type | Place | Place | Address |"):
            in_table = True
            continue
        if not line.startswith("|"):
            in_table = False
            continue
        if in_table:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 6:
                continue
            if cells[0] == ":-:" or all(c == "" for c in cells):
                continue
            if not cells[0] or not cells[3]:  # need type + address
                continue
            places.append({
                "type": cells[0],
                "name_kr": cells[1],
                "name_en": cells[2] or cells[1],
                "address": cells[3],
                "google_url": cells[4].replace("\\&", "&"),
                "notes": cells[6] if len(cells) > 6 else "",
                "region": detect_region(cells[3]),
                "source": "main_list",
            })
    return places


def parse_jeju_places(sheet_text):
    """Parse the Jeju 'Location | Type | KR | EN | Notes | Links' table."""
    places = []
    lines = sheet_text.split("\n")
    in_table = False
    for line in lines:
        line = line.strip()
        if line.startswith("| Location | Type | Places |"):
            in_table = True
            continue
        if not line.startswith("|"):
            in_table = False
            continue
        if in_table:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 5:
                continue
            if cells[0] == ":-:" or all(c == "" for c in cells):
                continue
            if not cells[2]:  # need at least a Korean name
                continue
            places.append({
                "type": cells[1] or "Other",
                "name_kr": cells[2],
                "name_en": cells[3] or cells[2],
                "address": "",  # Jeju table has no addresses
                "google_url": "",
                "notes": cells[4] if len(cells) > 4 else "",
                "region": "Jeju",
                "subregion": cells[0],
                "source": "jeju_list",
            })
    return places


def detect_region(address):
    if not address:
        return "Unknown"
    if address.startswith("서울") or "서울특별시" in address:
        return "Seoul"
    if address.startswith("경기") or "경기도" in address:
        return "Gyeonggi"
    if address.startswith("인천"):
        return "Incheon"
    if address.startswith("부산"):
        return "Busan"
    if address.startswith("대전"):
        return "Daejeon"
    if address.startswith("강원"):
        return "Gangwon"
    if "경상북도" in address or "경주" in address:
        return "Gyeongsangbuk-do"
    if "충청남도" in address or "공주" in address or "부여" in address:
        return "Chungcheongnam-do"
    if "전북" in address or "전주" in address:
        return "Jeollabuk-do"
    if "제주" in address:
        return "Jeju"
    return "Other"


def detect_district(address):
    """Pull the gu (district) from a Korean address for Seoul clustering."""
    if not address:
        return ""
    m = re.search(r"(\S+구)", address)
    return m.group(1) if m else ""


def load_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def geocode(query, cache):
    """Single Nominatim lookup with caching. Returns (lat, lng) or None."""
    if query in cache:
        return cache[query]
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "kr",
        "accept-language": "en",
    }
    url = f"{NOMINATIM}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if data:
                result = (float(data[0]["lat"]), float(data[0]["lon"]))
                cache[query] = result
                return result
            break  # empty result -> cache as miss
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 60 * (attempt + 1)
                print(f"  429 rate limit; sleeping {wait}s")
                time.sleep(wait)
                continue
            try:
                print(f"  HTTPError {e.code} for query (skipped): {e}")
            except Exception:
                pass
            break
        except Exception as e:
            try:
                print(f"  geocode error (skipped): {e}")
            except Exception:
                pass
            break
    cache[query] = None
    return None


def geocode_place(place, cache):
    """Try multiple query strategies. Return (lat, lng) or None."""
    candidates = []
    # Korean address (most precise)
    if place.get("address"):
        candidates.append(place["address"])
    # English name + region for Jeju / no-address entries
    if place.get("name_en"):
        suffix = " Jeju" if place.get("region") == "Jeju" else " South Korea"
        candidates.append(place["name_en"] + suffix)
    # Korean name as last resort
    if place.get("name_kr"):
        candidates.append(place["name_kr"])

    for q in candidates:
        was_cached = q in cache
        result = geocode(q, cache)
        if not was_cached:
            time.sleep(1.5)  # nominatim asks for >=1 req/sec; give buffer
        if result:
            place["geocode_query"] = q
            return result
    return None


def main():
    sheet_text = SHEET_PATH.read_text(encoding="utf-8")
    main_places = parse_main_places(sheet_text)
    jeju_places = parse_jeju_places(sheet_text)
    all_places = main_places + jeju_places
    # dedupe by (name_kr, address)
    seen = set()
    deduped = []
    for p in all_places:
        key = (p["name_kr"], p.get("address", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)

    # add district for clustering
    for p in deduped:
        p["district"] = detect_district(p.get("address", ""))

    print(f"Parsed {len(deduped)} unique places ({len(main_places)} main, {len(jeju_places)} Jeju)")

    cache = load_cache()
    geocoded = []
    failed = []
    for i, place in enumerate(deduped, 1):
        print(f"[{i}/{len(deduped)}] {place['name_en']} ...", end=" ", flush=True)
        result = geocode_place(place, cache)
        if result:
            place["lat"], place["lng"] = result
            geocoded.append(place)
            print("OK")
        else:
            failed.append(place)
            print("FAIL")
        if i % 10 == 0:
            save_cache(cache)

    save_cache(cache)
    OUT_PATH.write_text(json.dumps(geocoded, ensure_ascii=False, indent=2), encoding="utf-8")
    FAILED_PATH.write_text(json.dumps(failed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGeocoded: {len(geocoded)} / {len(deduped)} ({len(failed)} failed)")
    print(f"Output: {OUT_PATH}")


if __name__ == "__main__":
    main()
