import os
import shutil

ROOT_DIR = r"c:\Users\risha\OneDrive\Desktop\Foorplandata"
OUTPUTS_DIR = os.path.join(ROOT_DIR, "sample_outputs")

os.makedirs(OUTPUTS_DIR, exist_ok=True)

# List of generated demo/sample images in root to organize into sample_outputs
image_extensions = [".png", ".svg"]

files_moved = []
for filename in os.listdir(ROOT_DIR):
    filepath = os.path.join(ROOT_DIR, filename)
    if os.path.isfile(filepath):
        _, ext = os.path.splitext(filename)
        # Move generated demo/active/sample images
        if ext.lower() in image_extensions:
            dest_path = os.path.join(OUTPUTS_DIR, filename)
            shutil.move(filepath, dest_path)
            files_moved.append(filename)

print(f"Organized {len(files_moved)} image/output files into sample_outputs/ folder:")
for f in files_moved:
    print(f"  - {f}")
