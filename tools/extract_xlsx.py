"""Decode the base64 XLSX blob from the Drive MCP download into sheet.xlsx."""
import base64
import json
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(r"C:\Users\micha\.claude\projects\C--Users-micha-OneDrive\cba9c514-3a43-46ad-a91c-b754d4714adc\tool-results\mcp-29f121a3-4f62-427b-aafa-10a59a4b41ef-download_file_content-1776615426630.txt")
OUT = HERE / "sheet.xlsx"

obj = json.loads(SRC.read_text(encoding="utf-8"))
b64 = obj["content"][0]["embeddedResource"]["contents"]["blob"]
data = base64.b64decode(b64)
OUT.write_bytes(data)
print(f"wrote {OUT}: {len(data):,} bytes")
