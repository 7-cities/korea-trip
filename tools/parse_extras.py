"""
Parse the three sheet sections we missed:
  1) Top 3-col Location/Type/Place table (~40 entries)
  2) K-Traditional/Tour 5-col table (~6 entries)
  3) Eliana's List 3-col at the end (~4+ entries)
Dedup against existing places.json by Korean name OR English name (case-insensitive substring).
Writes extras_to_geocode.json (new unique entries needing coords).
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent

ROOT = HERE.parent

WEB = ROOT / "web"
SHEET = HERE / "sheet_raw.md"
EXISTING = ROOT / "places.json"
OUT = HERE / "extras_to_geocode.json"


def split_row(line):
    return [c.strip() for c in line.strip("|").split("|")]


def parse_top_list(text):
    """3-col: Location | Type | Place name (mixed KR/EN)."""
    out = []
    in_table = False
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("| Location | Type |  |"):
            in_table = True
            continue
        if not s.startswith("|"):
            in_table = False
            continue
        if in_table:
            cells = split_row(s)
            if len(cells) < 3 or cells[0] == ":-:" or not cells[2]:
                continue
            name = cells[2]
            # strip trailing URLs that snuck into the name
            name_clean = re.sub(r"\s*\(?https?://\S+\)?", "", name).strip()
            if not name_clean:
                continue
            out.append({
                "type": cells[1] or "Other",
                "name_kr": "",
                "name_en": name_clean,
                "address": "",
                "google_url": "",
                "notes": cells[0],  # use Location as note (e.g. "Seongsu", "Mapo(West)")
                "region": "Seoul",  # all in this section are Seoul-area or close
                "source": "top_list",
            })
    return out


def parse_ktraditional(text):
    """5-col: Type | KR | EN | Notes | Link."""
    out = []
    in_table = False
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("| Type |  |  | Notes |"):
            in_table = True
            continue
        if not s.startswith("|"):
            in_table = False
            continue
        if in_table:
            cells = split_row(s)
            if len(cells) < 5 or cells[0] == ":-:":
                continue
            name_kr = cells[1]
            name_en = cells[2] or name_kr
            if not name_kr and not name_en:
                continue
            link = cells[4].replace("\\&", "&") if len(cells) > 4 else ""
            out.append({
                "type": cells[0] or "Other",
                "name_kr": name_kr,
                "name_en": name_en,
                "address": "",
                "google_url": "",
                "notes": cells[3] or "",
                "web_link": link,
                "region": "Seoul",
                "source": "k_traditional",
            })
    return out


def parse_elianas(text):
    """3-col: Name | Google Maps (a category-ish word) | Description."""
    out = []
    in_table = False
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("| Name | Google Maps | Description |"):
            in_table = True
            continue
        if not s.startswith("|"):
            in_table = False
            continue
        if in_table:
            cells = split_row(s)
            if len(cells) < 3 or cells[0] == ":-:" or not cells[0]:
                continue
            out.append({
                "type": cells[1] or "Other",
                "name_kr": "",
                "name_en": cells[0],
                "address": "",
                "google_url": "",
                "notes": cells[2] or "",
                "region": "Seoul",
                "source": "elianas_list",
            })
    return out


def is_dup(new_p, existing):
    """Match on name_en or name_kr substring (lowercased), tolerant of small variants."""
    new_en = (new_p.get("name_en") or "").lower().strip()
    new_kr = (new_p.get("name_kr") or "").strip()
    for ex in existing:
        ex_en = (ex.get("name_en") or "").lower().strip()
        ex_kr = (ex.get("name_kr") or "").strip()
        if new_kr and ex_kr and (new_kr in ex_kr or ex_kr in new_kr):
            return True
        if new_en and ex_en and (new_en == ex_en):
            return True
        # substring only when long enough to be specific
        if new_en and ex_en and len(new_en) >= 8 and (new_en in ex_en or ex_en in new_en):
            return True
    return False


def main():
    text = SHEET.read_text(encoding="utf-8")
    existing = json.loads(EXISTING.read_text(encoding="utf-8"))

    a = parse_top_list(text)
    b = parse_ktraditional(text)
    c = parse_elianas(text)
    print(f"Parsed: top={len(a)}, k_traditional={len(b)}, elianas={len(c)}")

    all_new = a + b + c
    unique = []
    dup_count = 0
    for p in all_new:
        if is_dup(p, existing) or is_dup(p, unique):
            dup_count += 1
            continue
        unique.append(p)

    print(f"After dedup: {len(unique)} unique new (skipped {dup_count} duplicates)")
    OUT.write_text(json.dumps(unique, ensure_ascii=False, indent=2), encoding="utf-8")
    print("By source:")
    from collections import Counter
    for src, n in Counter(p["source"] for p in unique).items():
        print(f"  {src}: {n}")


if __name__ == "__main__":
    main()
