import json
from pathlib import Path
rows = json.loads((Path(__file__).parent / "sheet_hyperlinks.json").read_text(encoding="utf-8"))
jeju = [r for r in rows if r["sheet"] == "Jeju Island"]
print(f"Jeju rows: {len(jeju)}")
print()
# Show structure of first 10 + sample later rows
for r in jeju[:8]:
    print(f"row {r['row']} ({len(r['values'])} cols)")
    for i, v in enumerate(r["values"]):
        if v:
            link = r["links"].get(str(i), "")
            link_s = f"  [link={link[:60]}]" if link else ""
            s = repr(v)[:80]
            print(f"  col{i}: {s}{link_s}")
    print()
