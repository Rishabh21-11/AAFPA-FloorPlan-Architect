import zipfile, os
from pathlib import Path

print("=== RPLAN INSPECTION ===")
if os.path.exists("RPLAN_dataset.zip"):
    with zipfile.ZipFile("RPLAN_dataset.zip", "r") as z:
        infolist = z.infolist()
        print(f"RPLAN_dataset.zip: {len(infolist)} files")
        for f in infolist[:10]:
            print(f"  {f.filename} ({f.file_size} bytes)")

print("\n=== CUBICASA5K INSPECTION ===")
cb_path = Path("cubicasa5k")
if cb_path.exists():
    files = list(cb_path.rglob("*"))
    print(f"cubicasa5k: {len(files)} items")
    for f in files[:10]:
        size_str = str(f.stat().st_size) if f.is_file() else "DIR"
        print(f"  {f.relative_to(cb_path)} ({size_str})")

print("\n=== AAFPA MODULES INSPECTION ===")
aafpa_path = Path("aafpa")
if aafpa_path.exists():
    py_files = sorted(list(aafpa_path.glob("*.py")))
    for p in py_files:
        print(f"  {p.name} ({p.stat().st_size} bytes, {len(p.read_text(encoding='utf-8', errors='ignore').splitlines())} lines)")
