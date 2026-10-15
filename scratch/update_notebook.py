import json
import sys

def update_notebook():
    nb_path = 'AAFPA_FloorPlan_Architect.ipynb'
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # Read the new cell 35 source code
    with open('scratch/new_cell35.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract NEW_CELL_35_SOURCE
    # Look for NEW_CELL_35_SOURCE = r""" ... """
    start_marker = 'NEW_CELL_35_SOURCE = r"""'
    start_pos = content.find(start_marker)
    if start_pos == -1:
        raise ValueError("Could not find start marker in new_cell35.py")
    start_pos += len(start_marker)
    end_pos = content.rfind('"""')
    new_cell_35_text = content[start_pos:end_pos].strip()

    # Split into lines preserving line breaks as standard in ipynb source
    cell_35_source = [line + '\n' for line in new_cell_35_text.split('\n')]
    if cell_35_source:
        cell_35_source[-1] = cell_35_source[-1].rstrip('\n') # last line typically no trailing newline

    # Cell 35 update
    nb['cells'][35]['source'] = cell_35_source

    # Cell 36: Make sure it launches the interactive studio
    nb['cells'][36]['source'] = [
        "# Launch the Interactive Floor Plan Studio UI inside Notebook\n",
        "launch_interactive_studio()"
    ]

    # Cell 37: Replace terminal input console with a non-blocking interactive helper / instruction cell
    nb['cells'][37]['source'] = [
        "# SECTION 24B -- NOTEBOOK INTERACTIVE WORKSPACE\n",
        "# (All interactive floor plan generation and modifications are handled directly in the UI above)\n",
        "# You can also run the studio or test commands directly from Python in a non-blocking way:\n",
        "\n",
        "from aafpa import aafpa_chat, aafpa_select_layout, aafpa_finalize\n",
        "\n",
        "# Example programmatic interaction (or use the interactive UI widgets above):\n",
        "# res = aafpa_chat('Make the master bedroom bigger')\n",
        "print('✓ Interactive Studio is active in Section 24 cell above. No terminal input required.')"
    ]

    # Check all other cells for any unwanted input() calls
    for idx, cell in enumerate(nb['cells']):
        src = "".join(cell.get('source', []))
        if 'input(' in src and idx not in [35, 36, 37]:
            print(f"Warning: input() found in cell {idx}: {src[:100]}...")

    with open(nb_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)

    print("Successfully updated AAFPA_FloorPlan_Architect.ipynb!")

if __name__ == '__main__':
    update_notebook()
