# 🏛️ AAFPA 2.0 — AI Agentic Floor Plan Architect

**AAFPA 2.0** is an intelligent, condition-grounded architectural assistant for generative floor plan design, multi-turn conversational editing, and NBC 2016 constraint validation.

---

## 📁 Project Structure

```text
Foorplandata/
├── aafpa/                               # Core Python package
│   ├── smart_agent.py                   # ConditionGroundedSmartAgent (Spatial reasoning & diagnosis)
│   ├── studio.py                        # Studio Session Manager (Two-Phase Commit Protocol)
│   ├── architect_engine_tools.py        # Typed Geometric Tools Facade
│   ├── geometry_engine.py               # Parametric Geometry & Layout Engine
│   ├── dataset_pipeline.py              # HouseMind, RPLAN & CubiCasa5K Unified Loader
│   ├── ontology.py                      # Canonical Architectural Schema & Vocabulary
│   ├── actions.py                       # Structured Architectural Action IR
│   ├── spatial_reasoning.py             # Adjacency, Cardinal Orientation & Relative Placement
│   ├── rag_engine.py                    # Semantic RAG Engine & NBC Rules Knowledge Base
│   ├── semantic_agent.py                # Legacy Semantic Parser & Plan Memory
│   ├── evaluation.py                    # 13-Metric Benchmark Suite
│   └── interactive_cli_studio.py        # Terminal studio interface
│
├── AAFPA_FloorPlan_Architect.ipynb      # Main Jupyter Notebook with Interactive Design Studio
├── PRD_Agentic_AI_Floor_Plan_Architect.md # Complete Architectural PRD Specification
├── requirements.txt                     # Dependencies list
│
├── data_test.zip                        # HouseMind Dataset
├── RPLAN_dataset.zip                    # RPLAN Dataset
├── cubicasa5k/                          # CubiCasa5K Dataset (if included)
│
├── aafpa_conversational_model.json      # Trained Conversational Intent Model
├── conversational_instruction_dataset.json # Instruction fine-tuning dataset
│
├── interactive_web_studio.py            # Standalone Browser Web GUI Studio
├── interactive_cli_studio.py            # Standalone Terminal Studio
├── demo_aafpa2_walkthrough.py           # End-to-end Python demo script
├── tests/                               # Test suite & mock fixtures
└── sample_outputs/                      # Generated floor plans & demo visualizations
```

---

## 🚀 Quick Setup & Run Instructions

### 1. Requirements
Ensure you have **Python 3.10+** installed.

### 2. Install Dependencies
Open a terminal in this directory and run:
```bash
pip install -r requirements.txt
```

### 3. Running the Interactive Studio (Jupyter Notebook / VS Code)
1. Open **`AAFPA_FloorPlan_Architect.ipynb`** in VS Code or Jupyter Lab.
2. Select your Python kernel.
3. Run the setup cells, then run **Section 24 (`launch_interactive_studio()`)**.
4. The interactive design studio UI appears directly inside the notebook cell!
   - Describe requirements (e.g., *"3BHK on a 1500 sqft plot with modular kitchen"*).
   - Click **`[Select Layout X]`** on one of the 4 generated cards.
   - Type modifications into the chat box (e.g., *"Make master bedroom bigger"*, *"Now make it wider"*, *"Undo"*).

### 4. Running the Standalone Web GUI (Optional)
```bash
python interactive_web_studio.py
```
Open your browser at `http://localhost:8000`.

### 5. Running the Python Demo / Tests (Optional)
```bash
python demo_aafpa2_walkthrough.py
python -m unittest discover tests
```
