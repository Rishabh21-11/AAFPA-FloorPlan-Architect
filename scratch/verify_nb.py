import json
import sys
import os
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath('.'))

with open('AAFPA_FloorPlan_Architect.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells in notebook: {len(nb['cells'])}")
found_actual_call = False
for idx, cell in enumerate(nb['cells']):
    src = "".join(cell.get('source', []))
    for line_idx, line in enumerate(src.split('\n')):
        # remove comments
        code_part = line.split('#')[0]
        if re.search(r'(?<![a-zA-Z0-9_\'\"\.])input\s*\(', code_part):
            print(f"Cell {idx} line {line_idx+1} contains input() call: {line.strip()}")
            found_actual_call = True

if not found_actual_call:
    print("[PASS] Zero input() function calls found across all notebook cells!")
else:
    print("[FAIL] Found input() calls.")

# Test executing Cell 35 code in Python
cell35_code = "".join(nb['cells'][35]['source'])
try:
    scope = {}
    exec(cell35_code, scope)
    print("[PASS] Cell 35 compiled and executed successfully!")
    if 'launch_interactive_studio' in scope:
        print("[PASS] launch_interactive_studio function is defined.")
        # Call it headlessly
        scope['launch_interactive_studio']()
        print("[PASS] launch_interactive_studio() called successfully without error!")
except Exception as e:
    print("[FAIL] Error executing Cell 35:", e)
    import traceback
    traceback.print_exc()
