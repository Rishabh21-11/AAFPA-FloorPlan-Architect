import json

nb = json.load(open('AAFPA_FloorPlan_Architect.ipynb', encoding='utf-8'))
for idx in [34, 35, 36, 41, 42]:
    if idx < len(nb['cells']):
        c = nb['cells'][idx]
        print(f"=== CELL {idx} ({c.get('cell_type')}) ===")
        src = "".join(c.get("source", []))
        print(src[:800].encode("ascii", "replace").decode("ascii"))
        print("...")
