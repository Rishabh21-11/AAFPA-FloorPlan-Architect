import sys
import json
from pathlib import Path

nb_path = Path("AAFPA_FloorPlan_Architect.ipynb")
if nb_path.exists():
    data = json.loads(nb_path.read_text(encoding="utf-8"))
    print(f"Total cells: {len(data.get('cells', []))}")
    for idx, cell in enumerate(data.get('cells', [])):
        src = "".join(cell.get("source", []))
        summary = src.replace("\n", " ")[:90].encode("ascii", "replace").decode("ascii")
        print(f"Cell {idx:02d} [{cell.get('cell_type')}]: {summary}")
