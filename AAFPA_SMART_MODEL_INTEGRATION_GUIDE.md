# AAFPA Smart Conversational Architect — Integration Guide

## 1. Overview & System Architecture

The **AAFPA Smart Conversational Architect** is the central intelligence and orchestration layer of the **AI Agentic Floor Plan Architect (AAFPA)** system. It operates directly between the Interactive Web Studio / User Interface and the autonomous AAFPA Architect Engine.

```
                           [ USER ]
                              │
                              ▼
               ┌──────────────────────────────┐
               │    INTERACTIVE WEB STUDIO    │
               │   (/api/chat, /api/select)   │
               └──────────────┬───────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │ SMART CONVERSATIONAL         │
               │ ARCHITECT (ConditionGrounded)│
               │ • Entity Memory ("it")       │
               │ • Preservation Extraction    │
               │ • Plan Condition Diagnosis   │
               │ • 200+ Category Taxonomy     │
               └──────────────┬───────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │ ARCHITECT ENGINE TOOL FACADE │
               │ • 16 Typed Tools             │
               │ • Two-Phase Commit Protocol  │
               └──────────────┬───────────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
   ┌───────────────────────┐     ┌───────────────────────┐
   │ GEOMETRY ENGINE       │     │ CONSTRAINT VALIDATOR  │
   │ • Parametric Mutation │     │ • NBC 2016 Minimums   │
   │ • Wall Alignment      │     │ • Non-overlap & Bounds│
   └───────────┬───────────┘     └───────────┬───────────┘
               └──────────────┬──────────────┘
                              ▼
               ┌──────────────────────────────┐
               │    PLAN MEMORY & RENDERER    │
               │ • Version History Snapshots  │
               │ • Real-time SVG Canvas       │
               └──────────────────────────────┘
```

---

## 2. Input & Output Schemas

### Input Payload to the Smart Model:
```json
{
  "user_request": "Make the master bedroom wider, but don't touch the kitchen.",
  "conversation_context": [
    {"role": "user", "content": "I want a 2BHK in 1000 sqft."},
    {"role": "assistant", "content": "Generated 4 layouts. Layout 2 activated."}
  ],
  "current_plan_state": {
    "version": 1,
    "topology": "central_corridor",
    "plot": {"width_ft": 38.0, "length_ft": 39.5, "area_sqft": 1500.0},
    "rooms": [
      {"id": "r1", "type": "living_room", "x": 0.0, "y": 0.0, "width": 16.0, "length": 18.0, "area": 288.0},
      {"id": "r5", "type": "master_bedroom", "x": 0.0, "y": 18.0, "width": 16.0, "length": 15.0, "area": 240.0},
      {"id": "r3", "type": "kitchen", "x": 22.0, "y": 0.0, "width": 16.0, "length": 10.0, "area": 160.0}
    ]
  },
  "engine_feedback": ""
}
```

### Required Output Format:
```json
{
  "architectural_diagnosis": "User requests width expansion on master_bedroom. Space available along corridor partition. Kitchen is locked under explicit preservation constraint.",
  "engine_orders": [
    {
      "command": "MODIFY_DIMENSION",
      "parameters": {
        "target_entity": "master_bedroom",
        "action": "EXPAND",
        "dimension": "width",
        "value": 2.0
      },
      "hard_constraints": [
        "PRESERVE:kitchen"
      ]
    }
  ],
  "engine_feedback_handling": "",
  "user_response": "I've increased the width of the master bedroom by 2 feet while keeping the kitchen dimensions completely locked."
}
```

---

## 3. Session State & Version History

The studio manages conversational sessions through `InteractiveFloorPlanStudioSession`:
- **State Transitions:** `initial` $\rightarrow$ `layout_selection` $\rightarrow$ `active_editing` $\rightarrow$ `finalized`.
- **Versioning:** Every successful modification creates `Version N+1`.
- **Undo / Redo:** Restores exact snapshot states from `PlanMemory.history` without regeneration.
- **Two-Phase Commit:** If validation reports any hard violation (`hard_violations > 0`), the edit is automatically rolled back, and the specific constraint violation is reported to the user.

---

## 4. Supported Architect Engine Tools

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `get_current_plan` | `include_apertures`, `include_spatial_graph` | Returns the full serialized geometric state. |
| `find_rooms` | `room_type`, `room_id`, `spatial_relation` | Queries active rooms in the current plan. |
| `resize_room` | `target_room`, `dimension`, `delta_ft`, `direction` | Surgically resizes width, length, or area. |
| `transfer_area` | `source_room`, `target_room`, `amount_sqft` | Transfers floor area between two rooms. |
| `add_room` | `room_type`, `area_sqft`, `relative_to_type` | Inserts standard or custom rooms into available space. |
| `remove_room` | `room_type`, `room_id` | Deletes a room and rebalances surrounding space. |
| `move_room` | `room_type`, `relative_to_type`, `spatial_relation` | Relocates a room relative to an anchor entity. |
| `swap_rooms` | `room_a`, `room_b` | Swaps positions and dimensions of two rooms. |
| `improve_objective` | `objective` (`spaciousness`, `ventilation`, `privacy`) | Applies condition-grounded architectural mutations. |
| `validate_plan` | `plan` | Deterministic verification against NBC 2016 codes. |
| `undo` / `redo` | None | Rolls backward or forward across version snapshots. |

---

## 5. Web UI & REST API Integration

The Interactive Web Studio (`interactive_web_studio.py`) runs a lightweight HTTP server on port 8000:
- **`POST /api/chat`**: Accepts `{ "prompt": "..." }` $\rightarrow$ returns `{ "status": "...", "explanation": "...", "plan": {...}, "version": N }`.
- **`POST /api/select`**: Accepts `{ "option": 1..4 }` $\rightarrow$ activates the chosen candidate layout.
- **Zero Terminal Dependency:** All interactions, selections, and continuous edits occur directly through the web UI and REST API.

---

## 6. Model Training & Update Procedure

1. **Dataset Generation:** Run `python -m aafpa.dataset_pipeline` to generate normalized examples across 200+ taxonomy categories.
2. **Instruction Tuning:** Fine-tune foundation model (e.g. Qwen-2.5-7B, Mistral-7B, or Llama-3.1-8B) using QLoRA with target modules `[q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]`.
3. **Evaluation Benchmark:** Run `python tests/test_conversational_scenarios.py` to evaluate intent accuracy, entity resolution, preservation compliance, and zero-hallucination rate.
