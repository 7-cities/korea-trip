"""Quick inspect of Naver List rows to understand current column structure."""
import json
from pathlib import Path

HERE = Path(__file__).parent
rows = json.loads((HERE / "sheet_hyperlinks.json").read_text(encoding="utf-8"))

print("=" * 80)
print("Naver List — first 12 rows (raw values + link map)")
print("=" * 80)
for r in [x for x in rows if x["sheet"] == "Naver List"][:12]:
    print(f"\nrow {r['row']}  ({len(r['values'])} cols)")
    for i, v in enumerate(r["values"]):
        link = r["links"].get(str(i), "")
        marker = f"  [link={link}]" if link else ""
        print(f"  col{i}: {v!r}{marker}")

print()
print("=" * 80)
print("Naver List rows 745-765 (newer additions)")
print("=" * 80)
for r in [x for x in rows if x["sheet"] == "Naver List" and 745 <= x["row"] <= 765]:
    print(f"\nrow {r['row']}")
    for i, v in enumerate(r["values"]):
        if v:
            link = r["links"].get(str(i), "")
            marker = f"  [link={link}]" if link else ""
            print(f"  col{i}: {v!r}{marker}")
