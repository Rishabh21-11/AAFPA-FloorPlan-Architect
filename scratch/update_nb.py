import json
from pathlib import Path

nb_file = Path("AAFPA_FloorPlan_Architect.ipynb")
nb = json.loads(nb_file.read_text(encoding="utf-8"))

# Check if interactive prompt cell already exists in cells
has_prompt_cell = any("run_interactive_prompt_console" in "".join(c.get("source", [])) for c in nb["cells"])

if not has_prompt_cell:
    new_cell = {
        "cell_type": "code",
        "execution_count": None,
        "id": "interactive_prompt_console_cell",
        "metadata": {},
        "outputs": [],
        "source": [
            "# SECTION 24B -- LIVE INTERACTIVE PROMPT CONSOLE (Accepts Real-Time User Input)\n",
            "# Enter your natural language requirements and prompts directly when prompted!\n",
            "\n",
            "import os, sys\n",
            "import matplotlib.pyplot as plt\n",
            "from IPython.display import Image, display\n",
            "from aafpa import get_studio_session\n",
            "from interactive_cli_studio import render_and_save_plan\n",
            "\n",
            "def run_interactive_prompt_console():\n",
            "    session = get_studio_session()\n",
            "    print('=' * 75)\n",
            "    print('🏛️ AAFPA 2.0 -- LIVE INTERACTIVE FLOOR PLAN ARCHITECT CONSOLE')\n",
            "    print('=' * 75)\n",
            "    print('Type your architectural requirements and prompts directly.')\n",
            "    print('Examples:')\n",
            "    print('  1. \"3BHK on a 1500 sqft plot with modular kitchen, 3 bedrooms, 2 bathrooms\"')\n",
            "    print('  2. \"Select layout 2\" (or just \"2\")')\n",
            "    print('  3. \"Make the master bedroom bigger\"')\n",
            "    print('  4. \"Actually make it wider instead of longer\"')\n",
            "    print('  5. \"Now move the attached bathroom beside it\"')\n",
            "    print('  6. \"undo\", \"redo\", \"finalize\", or \"exit\"')\n",
            "    print('=' * 75 + '\\n')\n",
            "\n",
            "    while True:\n",
            "        try:\n",
            "            user_input = input('Architectural Prompt (You) > ').strip()\n",
            "        except (KeyboardInterrupt, EOFError):\n",
            "            print('\\nExiting interactive studio. Goodbye!')\n",
            "            break\n",
            "\n",
            "        if not user_input:\n",
            "            continue\n",
            "        if user_input.lower() in ('exit', 'quit', 'q'):\n",
            "            print('Session ended. Thank you for designing with AAFPA 2.0!')\n",
            "            break\n",
            "\n",
            "        res = session.handle_message(user_input)\n",
            "        if 'candidates' in res and res.get('candidates'):\n",
            "            print('\\n[AI ARCHITECT]: Generated 4 distinct layout candidate options:')\n",
            "            for idx, c in enumerate(res['candidates']):\n",
            "                print(f\"  [{idx+1}] {c['title']} (Topology: {c['topology']})\")\n",
            "            print(\"\\n👉 To choose a layout, type: 'Select layout 1', '2', '3', or '4'.\\n\")\n",
            "        else:\n",
            "            explanation = res.get('explanation', 'Operation completed.')\n",
            "            print(f'\\n[AI ARCHITECT]: {explanation}')\n",
            "            if 'plan' in res and res['plan']:\n",
            "                plan = res['plan']\n",
            "                ver = getattr(plan, 'version', 1)\n",
            "                img_path = render_and_save_plan(plan, 'Active Working Floor Plan', version=ver)\n",
            "                try:\n",
            "                    display(Image(filename=img_path))\n",
            "                except Exception:\n",
            "                    pass\n",
            "\n",
            "# Run the interactive prompt console\n",
            "run_interactive_prompt_console()\n"
        ]
    }
    # Insert right after cell 36 (Section 24)
    nb["cells"].insert(37, new_cell)
    nb_file.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print("Successfully inserted interactive prompt console cell into AAFPA_FloorPlan_Architect.ipynb!")
else:
    print("Prompt cell already present.")
