import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('AAFPA_FloorPlan_Architect.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

cells = nb.get('cells', [])
cell = cells[35]
src = ''.join(cell.get('source', []))
# Write it to a file so we can read it cleanly
with open('scratch/cell35_full.txt', 'w', encoding='utf-8') as out:
    out.write(src)
print(f'Cell 35 length: {len(src)} chars, written to scratch/cell35_full.txt')

# Also check cells 33 and 36 for session init
for idx in [2, 3, 33, 36]:
    c = cells[idx]
    s = ''.join(c.get('source', []))
    print(f'\n=== Cell {idx} (first 600 chars) ===')
    print(s[:600])
