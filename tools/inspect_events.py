import json
from pathlib import Path
rows = json.loads((Path(__file__).parent / "sheet_hyperlinks.json").read_text(encoding="utf-8"))
for r in rows:
    if r["sheet"] != "EventsTickets":
        continue
    print(f"row {r['row']}:")
    for i, v in enumerate(r["values"]):
        if v:
            link = r["links"].get(str(i), "")
            link_s = f"  [link={link}]" if link else ""
            print(f"  col{i}: {v!r}{link_s}")
    print()
