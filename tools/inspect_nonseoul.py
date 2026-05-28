import json
from pathlib import Path
rows = json.loads((Path(__file__).parent / "sheet_hyperlinks.json").read_text(encoding="utf-8"))
ns = [r for r in rows if r["sheet"] == "Non-Seoul Areas"]
print(f"Non-Seoul Areas rows: {len(ns)}")
print()
for r in ns:
    nonempty = [(i, v) for i, v in enumerate(r["values"]) if v]
    if not nonempty:
        continue
    print(f"row {r['row']} ({len(nonempty)} non-empty cols)")
    for i, v in nonempty:
        link = r["links"].get(str(i), "")
        link_s = f"  [link={link[:80]}]" if link else ""
        s = repr(v)[:100]
        print(f"  col{i}: {s}{link_s}")
    print()
