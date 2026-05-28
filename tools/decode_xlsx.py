"""Decode the base64 content from the Drive download tool result into sheet.xlsx."""
import base64
import json
import shutil
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(r"C:\Users\micha\.claude\projects\C--Users-micha-OneDrive\12e21a51-9847-4d6b-ae35-9bbcf0522532\tool-results\mcp-29f121a3-4f62-427b-aafa-10a59a4b41ef-download_file_content-1779933281311.txt")
DST = HERE / "sheet.xlsx"
BACKUP = HERE / "sheet.prev.xlsx"

raw = SRC.read_text(encoding="utf-8")
obj = json.loads(raw)
b64 = obj["content"]
data = base64.b64decode(b64)

if DST.exists():
    shutil.copy2(DST, BACKUP)
DST.write_bytes(data)
print(f"Wrote {len(data):,} bytes -> {DST.name}  (mime: {obj.get('mimeType')})")
