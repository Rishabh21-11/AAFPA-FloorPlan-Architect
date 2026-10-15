# PRD: Agentic AI Floor-Plan Architect

**Version:** 1.0
**Status:** Draft for engineering implementation
**Prototype form factor:** Modular Jupyter / Google Colab notebook (`.ipynb`)
**Primary reference dataset:** CubiCasa5K (insufficient alone — see §13)

---

## 1. Executive Summary

The Agentic AI Floor-Plan Architect (AAFPA) converts natural-language housing requirements into a **structured, validated, and rendered 2D floor plan**, and supports **iterative conversational editing** of that plan without regenerating it from scratch.

The system is not a chatbot that "describes" a house, and not an image generator that "draws" something house-shaped. It is a **planning system whose source of truth is a structured spatial data model** (rooms, geometry, graph relationships, constraints). An LLM operates at the edges of the system — understanding user language and explaining outputs — while a deterministic rule engine, a constraint validator, and a geometric optimizer are responsible for everything that must be *correct* (dimensions, non-overlap, connectivity, code compliance).

The prototype targets a single-floor (with limited multi-floor support), small-to-mid-size Indian residential house, reflects Indian building-code/bye-law structure, and optionally supports Vastu as a clearly-labeled preference layer, never as a constraint that can override safety or legality.

---

## 2. Problem Statement

Turning a verbal description of housing needs ("2BHK, 1000 sq ft, good ventilation") into an architecturally valid floor plan currently requires a human architect to apply tacit domain knowledge: standard room sizes, code minimums, adjacency conventions, circulation logic, and iterative judgment. Existing AI floor-plan tools generally fall into two unsatisfying categories:

- **Pure generative-vision systems** (trained on datasets like CubiCasa5K/RPLAN) that output plausible-looking raster images or vector layouts, but carry no explicit, checkable notion of "is this legal/valid/what the user asked for," and cannot be edited via natural language without a full re-generation.
- **Pure LLM systems** that produce structured JSON or SVG "because the model was asked to," with no deterministic geometric or code validation — meaning they can silently hallucinate impossible dimensions, overlapping rooms, or nonexistent regulations.

There is no widely available system that unifies **language understanding + retrieval of real architectural knowledge + deterministic constraint validation + geometric optimization + persistent, editable structured state + explainability**, evaluated with metrics appropriate to a *structured generation* problem rather than a classification or vision problem.

---

## 3. Motivation

- Floor-plan generation is a canonical **structured generation + constraint satisfaction** problem, making it an excellent testbed for agentic AI system design (multi-agent orchestration, RAG, deterministic tool use, iterative state-aware editing).
- CubiCasa5K and adjacent datasets exist but were built for **vision tasks** (segmentation, symbol detection), not for **language-to-plan generation** — so a realistic project must explicitly bridge that gap rather than pretend the dataset already does it.
- Indian residential design has well-documented, if fragmented, standards (NBC 2016, Model Building Bye-Laws 2016, state/municipal bye-laws) that are rarely encoded into any open-source generative system. Encoding them explicitly, with jurisdiction and priority tags, is itself a contribution.
- A system that can **preserve prior state under edits** is materially harder — and materially more useful — than one-shot generation, and is a distinguishing, demo-able capability.

---

## 4. Vision

AAFPA behaves like a junior architectural assistant that:

1. Interviews the user only enough to remove ambiguity (not more).
2. Retrieves the relevant rules for the user's situation (room type, jurisdiction, building type).
3. Produces a **structured plan** — not just an image.
4. Validates that plan against a prioritized rule hierarchy, repairing violations automatically where feasible.
5. Renders a clean, labeled 2D floor plan from the structured plan.
6. Explains *why* it made its spatial decisions.
7. Accepts follow-up instructions ("move the kitchen," "add a pooja room," "enlarge the master bedroom without shrinking the kitchen") and edits the **existing** plan surgically, preserving everything not implicated by the edit.
8. Always frames output as a **conceptual design proposal requiring professional review**, never as a construction-ready or legally certified document.

---

## 5. Goals

- G1. Convert free-text housing requirements into a structured requirement object with explicit handling of missing/ambiguous fields.
- G2. Maintain a structured floor-plan representation (geometric + graph) as the single source of truth; treat images purely as a rendering of that state.
- G3. Encode a prioritized, source-tagged rule library (user requirements → legal/safety → basic validity → functional design → environmental quality → Vastu/preference).
- G4. Deterministically validate every generated or edited plan against hard and soft constraints; never let an LLM silently approve a plan that violates a hard constraint.
- G5. Support targeted, state-preserving conversational edits, not full regeneration.
- G6. Render a professional, labeled 2D floor plan (SVG-first) from the structured state.
- G7. Provide a multi-dimensional evaluation framework appropriate to structured spatial generation (not just accuracy).
- G8. Remain reproducible in a single Colab notebook, with realistic compute (no from-scratch LLM training, no multi-GPU training run required for the MUST-HAVE scope).

---

## 6. Non-Goals

- NG1. Producing construction-ready, structurally engineered, or legally certified drawings.
- NG2. Full multi-story, multi-unit (apartment complex), or commercial-building support in the initial prototype (single-floor houses are MUST-HAVE; multi-floor is SHOULD/NICE-HAVE, see §37).
- NG3. Training a foundation LLM from scratch (see §7 rationale).
- NG4. Guaranteeing universal applicability of a single set of building bye-laws across all Indian jurisdictions — the system must instead explicitly track jurisdiction and flag where a rule is not universal.
- NG5. Treating Vastu as an engineering or legal requirement.
- NG6. Photorealistic 3D rendering (2D vector floor plan only in this phase).

---

## 7. Target Users

- **Primary (demo/academic):** the developer/evaluator of this system — an AI/ML or computational-design researcher validating an agentic architecture end-to-end.
- **Secondary (illustrative persona):** a homeowner or self-builder in India doing early-stage space planning before engaging a professional architect.
- **Tertiary (illustrative persona):** a junior architect or draftsperson using the tool to rapidly generate a first-pass concept plan to iterate on manually.

---

## 8. User Stories

- As a homeowner, I want to describe my plot size and room needs in plain language so that I get a first-draft layout without hiring an architect for an initial concept.
- As a homeowner, I want the system to ask me only the questions it actually needs answered (e.g., plot orientation) rather than a long form.
- As a user, I want to see *why* a room was placed where it was (e.g., "kitchen placed adjacent to dining for service efficiency") so I can trust and evaluate the output.
- As a user, I want to say "move the kitchen next to the dining room" and have only the kitchen (and anything it structurally requires) change — not a brand-new house.
- As a user, I want to be told clearly when my requirements don't fit my plot, with a specific, minimal suggested change, instead of getting a broken or invalid plan.
- As a user, I want an optional Vastu-compliance view that is clearly separated from the structural/legal validity of the plan.
- As a researcher, I want every module (requirement extraction, retrieval, geometry, validation) independently testable and independently evaluable.
- As a researcher, I want a baseline ladder (rule-based → LLM-only → LLM+RAG → LLM+RAG+solver → full agentic system) so the value of each architectural component is measurable.

---

## 9. Functional Requirements

**FR-1 Requirement extraction.** Parse free text into a structured requirement schema (§14). Must handle partial/implicit information (e.g., "2BHK" implies 2 bedrooms, typically 2 bathrooms in Indian convention, but the system must not hard-assume without flagging the inference).

**FR-2 Clarification.** Identify only the missing fields that block generation (plot dimensions/shape, floor count, must-have rooms) and ask minimal, targeted questions — not a fixed questionnaire.

**FR-3 Knowledge retrieval.** For every constraint category relevant to the request, retrieve applicable rules via RAG with source, jurisdiction, and priority metadata (§18).

**FR-4 Room program generation.** Produce the list of rooms, their target areas/dimensions, and required attributes (attached/common, ventilation need, etc.) from requirements + retrieved standards.

**FR-5 Adjacency/zoning graph.** Produce a graph of required/preferred/forbidden adjacencies and a public/private/service zoning assignment before geometry is generated.

**FR-6 Geometry generation.** Convert the room program + graph into non-overlapping, boundary-respecting room polygons with door and window placements.

**FR-7 Constraint validation.** Independently (of the LLM) verify hard and soft constraints: area/dimension minimums, non-overlap, connectivity, adjacency satisfaction, egress, ventilation/lighting minimums, code compliance.

**FR-8 Repair/optimization.** When violations exist, attempt automatic repair via local search/optimization before surfacing failure to the user.

**FR-9 Rendering.** Render the validated structured plan as a labeled 2D SVG floor plan (walls, doors, windows, room labels, dimensions, areas, north arrow, legend).

**FR-10 Explanation.** Generate a natural-language explanation of key placement decisions, grounded in the structured plan and retrieved rules (not free hallucination).

**FR-11 Conversational modification.** Parse a follow-up instruction against the *existing* persisted plan; identify the minimal affected subgraph; regenerate only that subgraph; re-validate; re-render; explain the diff.

**FR-12 Best-location scoring.** For "add X" requests, generate multiple candidate placements and select via an explicit, inspectable scoring function (§22).

**FR-13 Infeasibility handling.** Detect infeasible requirement sets before/at generation time, explain the specific conflict, and propose the smallest change that would make the request feasible.

**FR-14 Vastu layer (optional).** When requested, retrieve and score Vastu compatibility as a separate, clearly labeled score — never blended into hard-constraint pass/fail.

**FR-15 Versioning.** Persist every plan revision (post-generation and post-edit) so a user can review what changed across turns.

---## 10. Non-Functional Requirements

- **NFR-1 Determinism of validation.** Given the same structured plan, the validator must return the same pass/fail result every time (no LLM in the validation critical path).
- **NFR-2 Reproducibility.** The notebook must run top-to-bottom on a fresh Colab runtime (CPU-only fallback must exist; GPU optional/accelerating, not required, for the MUST-HAVE scope).
- **NFR-3 Latency.** A single-plan generation should complete in well under a minute on Colab CPU for the deterministic pipeline; LLM calls (if using a hosted API) are the dominant latency source and should be minimized/batched.
- **NFR-4 Explainability.** Every hard-constraint failure and every automatic repair must be logged with a human-readable reason traceable to a specific rule ID.
- **NFR-5 Graceful degradation.** If RAG retrieval fails or returns nothing for a rule category, the system falls back to a small embedded default rule table rather than failing generation outright, and flags that a default (not jurisdiction-specific) rule was used.
- **NFR-6 Extensibility.** Adding a new room type, a new jurisdiction's bye-laws, or a new constraint category must not require changes to the geometry/validation core — only new rule-table entries and (if needed) new schema fields.
- **NFR-7 Auditability.** Every generated plan must be traceable to: the requirement object, the rule set version used, and the optimization run parameters.
- **NFR-8 Safety framing.** Every rendered/exported plan must carry a visible disclaimer that it is conceptual and requires professional/engineering review.

---

## 11. System Architecture

```
                              USER
                               │
                    Conversation Interface
                               │
                       Requirement Agent
                               │
                    Planner / Orchestrator ───────────────┐
                               │                            │
                 ┌─────────────┴──────────────┐             │
                 │                              │             │
          RAG Knowledge Layer          Existing Plan Memory   │
        (rules, sources, priority)     (persisted structured  │
                 │                        plan + version log) │
                 └─────────────┬──────────────┘             │
                               │                            │
                        Room Program                        │
                               │                            │
                       Adjacency / Zoning Graph              │
                               │                            │
                        Geometry Generator                   │
                               │                            │
                        Constraint Engine  ◄──── Rule Library (priority 0–5)
                               │
                    Optimization / Repair Loop
                               │
                          Validation Report
                               │
                    Structured Floor Plan (source of truth)
                               │
                     ┌─────────┴─────────┐
                     │                   │
               SVG Renderer     Explanation Generator (LLM, grounded)
                     │                   │
                     └─────────┬─────────┘
                               │
                              USER
```

**Feedback / edit loop:**

```
User Feedback
   → Modification Agent (interprets instruction against Existing Plan Memory)
   → Affected-Subgraph Extraction
   → Candidate Generation (local geometry search, scoped to affected rooms)
   → Constraint Engine (re-validate whole plan, not just the delta)
   → Optimization / Repair (scoped)
   → Updated Structured Plan (new version)
   → Renderer + Diff Explanation
   → User
```

Two invariants govern the whole architecture:

1. **The LLM never writes directly to the structured plan.** It writes to intermediate objects (requirement deltas, candidate scores' natural-language framing, explanations) that are validated or scored by deterministic code before being merged into the plan.
2. **The structured plan, not the image, is versioned.** The renderer is a pure function of plan state; nothing about "the current design" lives only in an image or only in conversation history.

---

## 12. Agent Architecture

Each "agent" below is a **logical module** — in the prototype these can be implemented as Python classes/functions orchestrated by the Planner, with the LLM invoked only inside modules that legitimately need language understanding or generation. This is *not* a proposal to run seven independent autonomous LLM agents chatting with each other — that would add latency and hallucination risk with no benefit for a domain this constrained.

| Agent | Uses LLM? | Responsibility | Output |
|---|---|---|---|
| Requirement Agent | Yes (extraction + clarification question generation) | NL → structured requirements; detect missing/ambiguous fields | `RequirementObject` |
| Knowledge/RAG Agent | Yes (query formulation) + retrieval (deterministic) | Fetch applicable rules with source/priority/jurisdiction | list of `Rule` objects |
| Planning Agent | Partial (zoning rationale in NL) mostly deterministic | Room list, adjacency graph, public/private/service zoning | `RoomProgram`, `AdjacencyGraph` |
| Geometry Agent | No | Coordinates, dimensions, wall boundaries, door/window placement | `GeometricPlan` |
| Constraint Validator | No | Check all hard/soft constraints deterministically | `ValidationReport` |
| Optimization Agent | No | Local search / solver-based repair of violations | revised `GeometricPlan` |
| Rendering Agent | No | Structured plan → SVG/PNG | image asset |
| Explanation Agent | Yes (grounded generation only) | NL explanation of decisions, citing rule IDs and plan facts | explanation text |
| Modification/Edit Agent | Yes (instruction parsing) + deterministic diff logic | Parse edit instruction → scoped change plan; invoke Planning/Geometry/Validator on the affected subgraph only | updated `GeometricPlan` |

The **Planner/Orchestrator** is the only component that sequences agent calls; agents do not call each other directly. This keeps the control flow inspectable and testable (each agent is a pure-ish function with a defined input/output contract), which matters for both debugging and the evaluation framework (§26).

---

## 13. Dataset Strategy

### 13.1 What CubiCasa5K actually is

CubiCasa5K is a set of ~5,000 real Finnish residential floor-plan **images**, manually annotated with:
- Room polygons and room-type labels (bedroom, kitchen, bathroom, etc.)
- Wall segments/junctions
- Icons/symbols (doors, windows, fixtures, appliances)
- SVG-based structured annotation (making it usable beyond raw pixel segmentation)

It was built primarily for **floor-plan image parsing** research (semantic segmentation, junction/wall detection, symbol/icon detection, and raster-to-vector reconstruction), not for language-conditioned generation.

### 13.2 What it is NOT sufficient for

- It has **no natural-language requirement text** attached to plans (no "user asked for 2BHK with good ventilation" ↔ plan pairs).
- Its plans are **Finnish residential norms**, not Indian dimensional/code conventions — room sizes, staircase conventions, and typical adjacencies differ meaningfully from Indian residential practice.
- It provides no explicit **constraint-satisfaction labels** (nothing says "this plan violates X standard") — validity has to be inferred, not read off.
- It does not include plot/setback/parking/Vastu-relevant orientation metadata.
- Its graph structure (who's adjacent to whom) has to be *derived* from geometry; it is not delivered as a ready adjacency graph.

### 13.3 Multi-source dataset table

| Dataset | Data Type | What It Provides | Use in Project | Limitations |
|---|---|---|---|---|
| **CubiCasa5K** | Raster images + SVG annotations | Room polygons, room types, wall/junction/icon annotations | Vision baseline (§21); derive room-type/dimension priors; auxiliary raster→structure parser | No text, non-Indian norms, no constraint labels |
| **Structured3D** | Synthetic 3D scenes w/ structured JSON | Room layouts, structured semantic annotations, some 3D/BIM-style structure | Reference for schema design (structured room/graph representation); potential geometry-diversity augmentation | Synthetic/non-residential-Indian bias; not directly text-conditioned |
| **RPLAN** (large-scale vector floor-plan dataset, referenced as a comparable resource) | Vectorized room boundaries + adjacency | Large corpus of vectorized layouts with room-type and boundary data | Geometry-generation priors; adjacency-graph statistics (which room types co-occur/adjoin) | Chinese-apartment norms; no text pairing; license/availability must be verified before use |
| **Graph-annotated derivatives (e.g., CubiGraph-style graph extractions from CubiCasa5K)** | Room adjacency graphs derived from CubiCasa5K | Explicit graph representation for a subset of CubiCasa5K plans | Training/validating the adjacency-graph module; graph-metric evaluation ground truth | Coverage limited to what's been graph-annotated; inherits CubiCasa5K's non-Indian bias |
| **NBC 2016 (National Building Code of India)** | Regulatory text (PDF) | Authoritative dimensional minimums, ventilation/lighting rules, egress, fire-safety provisions | Primary source for Priority-1 hard constraints (§20) | Not machine-structured; requires manual/LLM-assisted extraction into the rule schema, with human verification |
| **Model Building Bye-Laws 2016 (Govt. of India, Ministry of Housing & Urban Affairs)** | Regulatory text | Setbacks, FAR, parking norms, general bye-law structure that states/municipalities adapt | Priority-1 constraints; jurisdiction-flagging template | A *model* — actual binding rules vary by state/municipal corporation; must not be treated as universally binding |
| **Selected local/municipal bye-laws** (added incrementally, as available) | Regulatory text | City-specific setback/FAR/parking specifics | Jurisdiction-specific override entries in the rule table | Sparse coverage in prototype; most jurisdictions will fall back to Model Bye-Law defaults with an explicit "not jurisdiction-verified" flag |
| **Architectural design references** (standard architectural data handbooks, e.g., "Time-Saver Standards"-style compiled room-dimension references, and reputable Indian architecture practice guides) | Reference text/tables | Room-size conventions, ergonomic clearances, functional adjacency conventions (kitchen–dining, living–entrance, etc.) | Priority-2/3 rule table (basic validity + functional design) | Not India-regulatory; treated as *practice guidance*, tagged as such, not as code |
| **Vastu Shastra reference texts** | Reference text | Directional/zonal placement preferences | Priority-5 optional preference layer only | Explicitly non-regulatory; must never be conflated with code |
| **Synthetic generator (built in-project, §29)** | Generated (text + structured plan pairs) | The *only* source that actually pairs NL requirements with structured, validated plans | Primary supervised/prompting resource for requirement-extraction and modification-interpretation evaluation; fine-tuning data if fine-tuning is pursued | Synthetic distribution may not fully match real user phrasing; mitigated by paraphrase augmentation |

### 13.4 What each dataset trains vs. informs

- **Can CubiCasa5K train NL → floor plan directly?** No — there is no NL side to pair it with. It can only inform the **vision/parsing** auxiliary component (§21) and supply **empirical priors** (typical room-size distributions, typical adjacency frequencies) that seed the deterministic rule table and the synthetic generator's randomization ranges.
- **Can it help train room/object recognition?** Yes — directly, this is its designed purpose (room-type classification from segmented polygons, door/window/symbol detection).
- **Can it help create structured floor-plan representations?** Indirectly — its SVG annotations can be parsed into the project's schema (§15) as *reference examples*, useful for validating that the schema can represent real-world plans, and for the vision-baseline pipeline (image → structure).
- **Can it help train a graph representation?** Yes, once room polygons are extracted, an adjacency graph can be derived geometrically (shared-wall / doorway-connection heuristics) and used as graph-metric ground truth for a subset of plans.
- **Final unified dataset** is therefore **synthetic-primary, real-data-informed**: the synthetic generator (§29) produces the NL↔structured-plan↔validation pairs that actually drive requirement-extraction and evaluation, while CubiCasa5K/Structured3D/RPLAN-style resources inform (a) the vision baseline, (b) empirical priors for room-size/adjacency distributions used when generating synthetic data, and (c) sanity-checking that the schema is expressive enough for real plans.

### 13.5 Unified record schema (used across all sources after transformation)

```json
{
  "plot": {"width": 0, "length": 0, "shape": "rectangular", "orientation_deg": 0, "jurisdiction": "IN-<state>-<city>"},
  "building": {"floors": 1, "footprint_area": 0, "setbacks": {}},
  "rooms": [
    {"id": "", "type": "", "x": 0, "y": 0, "width": 0, "length": 0, "area": 0,
     "doors": [], "windows": [], "adjacent_to": [], "zone": "public|private|service"}
  ],
  "room_relationships": [{"a": "", "b": "", "relation": "adjacent|separated|near"}],
  "doors": [{"id": "", "room_a": "", "room_b": "", "width": 0, "position": {}}],
  "windows": [{"id": "", "room": "", "width": 0, "wall": "N|S|E|W", "position": {}}],
  "dimensions": {},
  "orientation": {},
  "ventilation": {"cross_ventilated_rooms": []},
  "lighting": {"naturally_lit_rooms": []},
  "circulation": {"paths": []},
  "constraints": [],
  "architectural_rules": [{"rule_id": "", "priority": "", "source": ""}],
  "user_requirements": {},
  "generated_plan": {},
  "validation": {"hard_violations": [], "soft_violations": [], "score": 0},
  "score": {}
}
```

Raw sources are transformed into this schema by source-specific adapters (a CubiCasa5K adapter parsing its SVG annotation into `rooms`/`doors`/`windows`/derived `room_relationships`; a regulatory-text adapter turning extracted rule statements into `architectural_rules` entries; the synthetic generator emitting the schema natively).

---

## 14. Data Schema (Runtime / Application Schema)

### 14.1 `RequirementObject` (output of Requirement Agent)

```json
{
  "plot_area_sqft": 1000,
  "plot_dimensions": {"width_ft": null, "length_ft": null, "confidence": "unspecified"},
  "floors": 1,
  "bedrooms": 2,
  "bathrooms": {"attached": 1, "common": 1},
  "must_have_rooms": ["living_room", "kitchen", "dining"],
  "optional_rooms": [],
  "preferences": {"ventilation": "good", "lighting": "good", "vastu": false},
  "jurisdiction": {"state": null, "city": null, "confidence": "unspecified"},
  "ambiguous_fields": ["plot_dimensions", "jurisdiction"],
  "missing_required_fields": []
}
```

### 14.2 `Rule` (output of RAG layer, see §18 for full spec)

### 14.3 `RoomProgram`, `AdjacencyGraph`, `GeometricPlan`, `ValidationReport` — see §19, §21, §22.

---

## 15. RAG Architecture

### 15.1 Knowledge sources (ingested at build time)

- NBC 2016 excerpts (habitable-room minimum area/width/height, ventilation-opening ratios, staircase width, egress).
- Model Building Bye-Laws 2016 excerpts (setbacks, FAR/ground coverage, parking norms by plot size).
- A small curated set of local/municipal bye-law excerpts (as available; explicitly scoped, not claimed exhaustive).
- Architectural practice references for room-size/adjacency conventions (Priority-2/3, tagged "practice guidance" not "code").
- Vastu reference material (Priority-5, tagged "preference," never "requirement").

### 15.2 Ingestion pipeline

1. **Chunking**: split source documents into rule-sized chunks (a clause/paragraph that expresses one checkable constraint where possible), preserving section/clause numbers for citation.
2. **Structuring**: an LLM-assisted extraction pass converts each chunk into a candidate `Rule` object (below); a **human-in-the-loop review step is required before any Priority-1 (legal) rule is marked verified** — this is a project requirement, not optional, to avoid inventing regulations (§34).
3. **Embedding**: embed chunk text (e.g., a sentence-transformer model) into a vector store (e.g., FAISS/Chroma for the Colab prototype).
4. **Indexing metadata**: each vector is stored with `{rule_id, source, source_type, jurisdiction, priority, applies_to, constraint_type, value, verified: bool}`.

### 15.3 `Rule` object

```json
{
  "rule_id": "NBC-HAB-001",
  "rule": "Minimum floor area of a habitable room shall not be less than 9.5 sq. m.",
  "source": "National Building Code of India 2016, Part 3",
  "source_type": "national_code",
  "priority": "HARD",
  "applies_to": ["bedroom", "living_room"],
  "constraint_type": "minimum_area",
  "value": 9.5,
  "unit": "sq_m",
  "jurisdiction": "India",
  "verified": true
}
```

### 15.4 Retrieval-time behavior

- Given a `RequirementObject`, the Knowledge Agent formulates targeted queries per constraint category (room dimensions for each requested room type, ventilation, egress, setback/parking if plot/building metadata implies applicability, jurisdiction-specific overrides if jurisdiction known).
- Retrieval returns top-k candidate rules per category; a deterministic re-ranker prefers **higher-specificity jurisdiction matches** (local > model bye-law > national default) and **higher `verified` status**.
- **Hard architectural rule:** retrieved text is never used to directly patch or override the deterministic Constraint Engine's rule table at runtime. Retrieval populates the Constraint Engine's active rule set *before* validation runs; it does not get to bypass validation after the fact. This preserves the "RAG informs, code enforces" boundary required by §13/§26.
- If retrieval returns conflicting rules (e.g., two municipal sources disagree), the higher-priority/higher-specificity source wins deterministically, and the conflict is logged and surfaces in the explanation ("local bye-law X used in preference to national default Y").

---

## 16. LLM / Transformer Architecture

### 16.1 Role definition

The LLM is used **only** where language understanding or language generation is the actual task:

| Task | LLM responsible? |
|---|---|
| A. Language understanding (parse free text → requirement fields) | **Yes** |
| B. Architectural reasoning about *what* a request implies (e.g., "2BHK" → likely 2 bathrooms) | Yes, but flagged as an *inference*, not asserted as user-stated |
| C. Retrieval query formulation | Yes (turns requirement fields into retrieval queries) |
| D. Plan generation (room program *drafting*, i.e., proposing candidate room lists) | Yes, but every proposal is validated/adjusted deterministically before being accepted |
| E. Geometric constraints (exact coordinates, collision) | **No** — deterministic geometry generator + optimizer |
| F. Validation (hard/soft constraint pass/fail) | **No** — deterministic Constraint Engine |
| G. Rendering | **No** — deterministic renderer |
| H. Iterative editing (interpreting *what the user means*) | **Yes** for interpretation; **No** for executing the geometric change, which goes through the same deterministic Geometry/Validator path as initial generation |

### 16.2 Model choice for the prototype

- Use an existing **pretrained instruction-tuned LLM via API or a locally-runnable open-weight model** (e.g., a modern mid-size open-weight instruct model runnable on Colab, or a hosted API call) for tasks A–D and H (interpretation half).
- **No foundation-model pretraining.** Rationale: pretraining a transformer from scratch requires data/compute scales (billions of tokens, many GPU-days) entirely disproportionate to a structured-domain task that is dominated by extraction and grounded generation, both of which pretrained instruct models already do well with the right prompting/structured-output constraints.
- **Fine-tuning:** not required for MUST-HAVE scope. It becomes justified (SHOULD-HAVE) only if few-shot/structured-prompting accuracy on requirement extraction and modification-instruction parsing (measured in §26) falls below an acceptable threshold on the synthetic evaluation set — in which case light instruction fine-tuning (e.g., LoRA) on the synthetic NL↔requirement pairs is the recommended, realistic next step, not full fine-tuning.
- **Structured output enforcement:** all LLM calls that must produce data consumed by deterministic code (RequirementObject, candidate room-program proposals, edit-instruction parses) use constrained/structured generation (JSON-schema-constrained decoding or strict prompt + schema validation with automatic re-ask on malformed output), never free text parsed by regex.

---

## 17. RNN Experiment

**Purpose:** academic completeness — demonstrate, not assume, that a Transformer/LLM is the right choice for the sequence-like sub-problem of room-placement ordering.

**Setup:** represent a floor plan as a token sequence, e.g. `ENTRANCE → LIVING → DINING → KITCHEN → BEDROOM_1 → BATH_ATTACHED_1 → BEDROOM_2 → BATH_COMMON`, derived from a breadth-first traversal of the adjacency graph starting at the entrance node. Train:

- An **LSTM/GRU** sequence model to predict the next room token (and coarse relationship label) given the prefix.
- A small **Transformer encoder-decoder** (or a prompted pretrained LLM in a few-shot setting) on the identical task/data.

**Comparison metrics:** next-token (next-room) accuracy, full-sequence exact-match rate, and — more importantly for this domain — **downstream validity**: what fraction of sequences, when converted to a candidate adjacency graph, satisfy the hard adjacency constraints from the rule library.

**Expected result and rationale (stated up front, to be confirmed empirically):** the RNN is expected to perform comparably on short sequences (room counts are small, ~5–10 rooms) since long-range dependency is not the bottleneck here, but the Transformer/LLM is expected to generalize better to **novel room combinations** (e.g., a pooja room + study room combination underrepresented in training) because it can be prompted/conditioned on the explicit requirement object rather than purely on sequence statistics, and because it can leverage retrieved rule text directly (RAG-conditioning), which an RNN architecture has no natural mechanism for.

**Disposition:** this experiment is a **NICE-TO-HAVE evaluation artifact** for the report/notebook (`19_RNN_Baseline`), explicitly **not** part of the production pipeline (§16 already assigns sequence/planning reasoning to the LLM-conditioned Planning Agent, not to a trained RNN). If the RNN outperforms on some narrow slice, that finding is reported, not silently discarded — but it does not change the production architecture unless it demonstrates a *decisive, reproducible* advantage on downstream validity, which is not expected given the small-sequence, rule-conditioned nature of the task.

---

## 18. Computer Vision Component

CubiCasa5K's natural fit is a **vision baseline and auxiliary capability**: `Floor Plan Image → Vision Model → Structured Floor Plan → Graph + Geometry`.

- **Room segmentation:** a semantic segmentation model (e.g., a U-Net-style architecture, feasible to train/fine-tune on Colab on a CubiCasa5K subset) predicts room-type masks.
- **Wall/junction detection:** reuse CubiCasa5K's own annotation conventions for wall-segment/junction ground truth; a lightweight detector (or the polygon boundaries between adjacent room masks) yields wall geometry.
- **Door/window/symbol detection:** an object-detection model (e.g., a small YOLO-style detector) trained on CubiCasa5K's icon annotations.
- **Raster → structured schema:** post-process segmentation + detections into the project's unified schema (§13.5): room polygons → `rooms[]`, detected doors/windows → `doors[]`/`windows[]`, shared-boundary heuristics → `room_relationships[]`.

**Use in the project:** (1) an **evaluation baseline** — "how well can we recover ground-truth structure from an existing real plan," useful for sanity-checking the schema's expressiveness and for a Baseline-0-style comparison point; (2) a **future-facing capability** — letting a user upload an existing plan image and have the system parse it into an editable structured plan, entering the same Conversation/Edit Agent pipeline as an AI-generated plan. Capability (2) is **SHOULD-HAVE**, not MUST-HAVE, for the initial prototype (§37).

---

## 19. Graph Representation

**Nodes:** rooms, entrance, doors, windows, stairs (if multi-floor), service areas (e.g., utility, parking).
**Edges (typed):** `adjacent`, `connected` (has a door between), `accessible` (reachable via circulation without passing through a private room), `attached` (bathroom attached to a specific bedroom), `near` (soft-preferred proximity, not a shared wall), `separated` (explicit non-adjacency requirement, e.g., kitchen not directly serving as bedroom's only access).

**Why both a geometric and a graph representation are necessary:**
- The **graph** is what makes *relational* reasoning (adjacency requirements, privacy zoning, circulation validity, "what changes are affected by moving the kitchen") tractable and fast — graph queries (neighbors, reachability, shortest path from entrance) are cheap and exactly what the rule engine's relational constraints (Priority 2–3) are phrased in terms of.
- The **geometry** is what makes *metric* reasoning (does this fit in the plot, do these two rooms overlap, is this window wide enough) tractable — metric constraints (Priority 1–2, environmental Priority 4) are phrased in terms of coordinates, areas, and distances that have no meaning in a graph alone.
- Editing operates on the graph first (what should change relationally) and then re-derives/repairs geometry (§25) — trying to reason about "move the kitchen closer to the dining room" directly in coordinate space, without a graph layer, would require re-deriving adjacency from scratch on every edit, which is exactly the wasteful "regenerate everything" behavior the project explicitly must avoid (§11).

**GNN usage:** a Graph Neural Network *could* learn to score candidate adjacency graphs or predict good room-graph completions from data. Given the **small graph sizes** (typically 5–12 nodes for a house) and the **explicit, enumerable rule set** already available, a full GNN is judged **not justified for the MUST-HAVE prototype** — a rule-scored/heuristic graph completion (§25 scoring function) achieves the same outcome with full explainability and no training data requirement. A GNN-based adjacency-graph scorer is recorded as a **FUTURE WORK** item (§36), useful once a large enough labeled corpus of "good vs. bad" adjacency graphs exists (plausibly bootstrapped from the synthetic generator after the fact).

---

## 20. Floor-Plan Generation Pipeline

```
Natural Language
   ↓  (Requirement Agent, LLM, structured-output constrained)
Requirement Extraction  → RequirementObject
   ↓  (deterministic schema validation)
Requirement Validation  → flags missing/ambiguous fields; triggers clarification Qs if blocking
   ↓  (Knowledge/RAG Agent)
RAG Retrieval  → active Rule set for this request (jurisdiction + room-type filtered)
   ↓  (Planning Agent, LLM-drafted + rule-checked)
Room Program  → list of RoomSpec {type, target_area, target_dims, zone, must/should adjacencies}
   ↓  (Planning Agent, deterministic scoring over candidate graphs)
Adjacency Graph  → typed graph per §19
   ↓  (Planning Agent, deterministic)
Spatial/Zoning Plan  → public/private/service zone regions within the plot boundary
   ↓  (Geometry Agent, deterministic + local optimization)
Geometry Generation  → room polygons, walls, door/window candidate positions
   ↓  (Constraint Validator, deterministic)
Constraint Validation  → ValidationReport {hard_violations, soft_violations, score}
   ↓  (Optimization Agent, deterministic search)
Optimization / Repair  → iterate geometry (and, if needed, room program) until hard violations = 0 or infeasibility is declared
   ↓
Final Structured Plan  (source of truth; versioned)
   ↓  (Rendering Agent, deterministic)
2D Rendering  → SVG (+ optional PNG export)
   ↓  (Explanation Agent, LLM, grounded in ValidationReport + Rule citations)
Explanation
```

**Stage notes:**
- *Requirement Validation* is a hard gate: generation does not proceed to RAG/room-program stages while a **blocking** field is missing (plot size/shape and floor count are blocking; jurisdiction and Vastu preference are non-blocking, defaulting to "unspecified/generic" with a flag).
- *Room Program* generation is where Priority-0 (user) requirements are asserted as hard targets; the LLM proposes but the deterministic layer checks that every explicit user requirement (bedroom count, bathroom count/type, named rooms) is represented before advancing.
- *Adjacency Graph* construction uses a deterministic scored search (§25) over candidate graphs satisfying Priority-2/3 rules, not free LLM graph generation, precisely because graph validity here is fully rule-checkable and doesn't benefit from LLM creativity.
- *Geometry Generation* uses a deterministic layout algorithm (e.g., a slicing-tree / rectangular-packing approach seeded by zone assignment and target areas — see §23) rather than an LLM predicting coordinates, because coordinate prediction is exactly the class of task (E in §16.1) explicitly reserved for deterministic methods.
- *Optimization/Repair* may adjust room dimensions within tolerance, reposition rooms, or (only if truly infeasible) drop/shrink a **soft** requirement — it must never silently drop a **hard** (Priority-0/1) requirement; if it cannot repair without violating a hard requirement, it returns to the Requirement stage with an infeasibility report (§9 FR-13).

---

## 21. Constraint Engine

### 21.1 Constraint categories checked

Overlap • connectivity/reachability • adjacency satisfaction (required/forbidden) • area/dimension minimums per room type • door width • window/opening ratio (ventilation) • natural-light minimums • cross-ventilation where required • egress path existence • circulation width • privacy (bedroom not used as sole through-route) • wet-area clustering/plumbing stack proximity • setback/FAR/parking (when plot/jurisdiction metadata is present) • staircase requirements (multi-floor only).

### 21.2 `ValidationReport`

```json
{
  "hard_violations": [
    {"rule_id": "NBC-HAB-001", "room": "bedroom_2", "detail": "area 8.1 sq.m < min 9.5 sq.m"}
  ],
  "soft_violations": [
    {"rule_id": "FUNC-ADJ-014", "detail": "kitchen not directly adjacent to dining (distance 2 rooms)"}
  ],
  "score": 0.0,
  "passed": false
}
```

### 21.3 Hard vs. soft vs. preference (execution semantics)

- **Hard** (Priority 0–1): a plan with any unresolved hard violation is **not** returned to the user as a final plan; it must go through repair/optimization or be reported as infeasible.
- **Soft** (Priority 2–3): penalized in the composite score (§26.7); optimization tries to minimize but a plan can be delivered with some soft violations if repair cannot eliminate them without breaking a hard constraint, and this is disclosed to the user.
- **Preference** (Priority 4–5, incl. Vastu): scored separately and reported separately; never blended into the pass/fail determination.

---

## 22. Architectural Rule Hierarchy

*(As specified in the source brief — restated here as the binding hierarchy for the Constraint Engine.)*

- **Priority 0 — User Requirements:** explicit counts/types/sizes the user stated. Satisfied whenever physically feasible; if infeasible, the conflict is explained (§9 FR-13), never silently dropped.
- **Priority 1 — Safety / Legal / Building Code:** sourced from NBC, Model Building Bye-Laws, and identified local bye-laws where available; jurisdiction must be tracked; a rule not verified as applicable to the user's jurisdiction is flagged as a **default**, not asserted as binding local law.
- **Priority 2 — Basic Architectural Validity:** dimension practicality, non-overlap, enclosure, reachability, logical door connections, practical circulation, basic bedroom privacy, bathroom accessibility, kitchen/bathroom ventilation, habitable-room lighting/ventilation, logical wet-area planning.
- **Priority 3 — Functional Design:** living-near-entrance, kitchen–dining relationship, bedroom separation from high-traffic paths, attached-bathroom direct access, common-bathroom access without crossing private bedrooms, plumbing/service efficiency, minimized-but-comfortable circulation, furniture-placement feasibility.
- **Priority 4 — Environmental Quality:** lighting, cross-ventilation, window placement, orientation, sun exposure/heat gain, airflow, courtyards/shafts where relevant.
- **Priority 5 — Vastu / User Preference:** retrieved and scored only when requested; explicitly never permitted to override Priorities 0–4; always reported as a distinct, labeled score.

Every rule entry in the library carries `priority` (0–5), `hard|soft|preference`, `source`, `source_type`, `jurisdiction`, `applies_to`, and, where numeric, `constraint_type`/`value`/`unit` — this is what allows the Constraint Engine to resolve conflicts **deterministically by priority** rather than by LLM judgment (§9).

---

## 23. Optimization Strategy

### 23.1 Geometry generation method

A **constrained rectangular-packing / slicing-tree approach**, seeded by the zoning plan: the plot is recursively partitioned (guillotine-cut style) into public/private/service zones, then into individual room slots sized toward each `RoomSpec`'s target area/aspect ratio, with corridor allocation reserved during partitioning (not squeezed in afterward). This is preferred over free-form/learned layout because it (a) guarantees non-overlap and full plot coverage by construction, (b) is fast and deterministic, and (c) is directly steerable by the zoning/adjacency graph the Planning Agent already produced.

### 23.2 Repair/optimization methods

| Method | Used for | Why |
|---|---|---|
| **Local search / hill-climbing** (swap adjacent partitions, nudge cut lines, resize within tolerance) | Default repair pass after validation | Cheap, fast, sufficient for the small search space of a single house (5–15 rooms) |
| **Simulated annealing** | Escaping local minima when hill-climbing plateaus with unresolved hard violations | Still cheap at this problem scale; only invoked as a second pass if hill-climbing fails |
| **Constraint Programming (CP-SAT style, e.g., via OR-Tools)** | Formal feasibility check when heuristic repair repeatedly fails, and for the "smallest change to make this feasible" suggestion (FR-13) | CP solvers can prove infeasibility and return a minimal conflicting subset, which heuristic search cannot guarantee |
| **Genetic Algorithm** | Recorded as an **alternative/optional** method for the geometry-generation stage itself, not required | Justified only if slicing-tree + local search proves insufficiently diverse in evaluation; adds complexity without a demonstrated need at MUST-HAVE scope |
| **Reinforcement Learning** | **Not used** | Requires a reward signal and training loop disproportionate to a problem already well-served by deterministic search + an explicit rule-checkable reward function; RL would be trading interpretability for no measurable benefit at this scale — recorded as FUTURE WORK only if the project later targets learned, style-diverse layout generation at scale |
| **Beam search** | Candidate room-program / adjacency-graph selection (§25) | Natural fit for scoring a modest number of discrete candidate configurations |

### 23.3 Composite objective (used for candidate ranking, not for hard pass/fail)

```
Score =
    w1 * RequirementSatisfaction
  + w2 * BuildingCompliance
  + w3 * GeometryQuality
  + w4 * Connectivity
  + w5 * Ventilation
  + w6 * Lighting
  + w7 * Circulation
  + w8 * Privacy
  + w9 * PlumbingEfficiency
  + w10 * VastuPreference        (only included if user requested Vastu; else w10 = 0)
  - w11 * ConstraintViolations   (soft violations only — hard violations gate the plan before scoring, not merely penalize it)
```

- **Hard-coded weights (defaults):** `w1..w9` initialized from domain judgment (Requirement Satisfaction and Building Compliance weighted highest, since they map to Priority 0–1) and documented in a single config cell in the notebook — these are the MUST-HAVE default.
- **Tunable/learnable weights:** exposed as configuration; a SHOULD-HAVE extension is to fit `w1..w10` against a small human-rated preference set (pairwise plan comparisons) using a simple ranking loss — recorded as future refinement, not required for the initial prototype.
- `w11` and hard-violation gating are **never** tunable to zero by configuration drift — the notebook enforces `hard_violations == 0` as a non-negotiable precondition for returning a "final" plan, independent of the composite score.

---

## 24. Iterative Editing Architecture

### 24.1 Persistent state

Every session maintains a `PlanMemory`: the current `GeometricPlan` + `AdjacencyGraph` + `RequirementObject` + version history (list of prior `GeometricPlan` snapshots with the edit instruction that produced each).

### 24.2 Modification pipeline

```
Existing Plan (PlanMemory)
   ↓
Modification Agent (LLM parses instruction into a structured EditIntent)
   ↓
EditIntent → {operation: add|remove|resize|move|convert|improve,
              target: room_id or room_type or "new",
              constraints: e.g. "don't reduce kitchen", "near entrance"}
   ↓
Affected-Subgraph Extraction (deterministic): identify the minimal set of rooms/edges
   the EditIntent touches, plus any rooms structurally adjacent to that set
   ↓
Candidate Generation (deterministic, scoped to the affected subgraph only —
   the rest of the plan's geometry/graph is held fixed as a constraint)
   ↓
Candidate Scoring (§25 scoring function, plus any EditIntent-specific constraints
   such as "kitchen area must not decrease")
   ↓
Selected Candidate → merge into full plan
   ↓
Constraint Engine (validates the FULL plan, not just the delta — an edit
   must not silently introduce a violation elsewhere)
   ↓
Optimization/Repair (scoped preferentially to the affected subgraph; only
   expands scope if repair is otherwise impossible, and this expansion is disclosed)
   ↓
New PlanMemory version + Diff Explanation ("kitchen moved from (x,y) to (x',y'); dining, living unchanged")
```

### 24.3 Supported edit operations (MUST-HAVE set)

add room • remove room • resize room • move room • change room type/conversion • improve ventilation (local) • improve Vastu compatibility (re-score/re-suggest only, never silently move rooms for Vastu without confirmation, since Vastu is Priority 5).

### 24.4 Supported edit operations (SHOULD/NICE-HAVE set)

add balcony • add parking • add staircase • change entrance • change orientation • add/remove floor. These require larger structural changes (footprint/zoning-level, not room-level) and are scoped as SHOULD-HAVE (single added structural element) or NICE-HAVE (multi-floor operations) per §37.

### 24.5 Why full-plan re-validation but scoped candidate generation

Scoping *generation* to the affected subgraph is what avoids "regenerate the whole house" (the explicit failure mode called out in the brief). But scoping *validation* the same way would risk missing a second-order violation (e.g., moving the kitchen breaks a plumbing-clustering rule with the bathroom on the other side of the plot) — so validation always runs against the complete, merged plan, while generation search space stays small and disruption stays minimal by construction (the optimizer's objective includes a **disruption penalty**: total geometric change relative to the pre-edit plan, so among equally valid candidates the least-disruptive one wins).

---

## 25. Rendering System

- **Primary format: SVG**, generated directly from the structured plan's coordinates (not from a bitmap/ML image model) — this guarantees the rendering is always a faithful, to-scale depiction of the source-of-truth plan.
- **Elements rendered:** external walls (heavier stroke), internal walls, room fill by zone/type with a legend, room labels with type + computed area, door swings, window markers, entrance marker, north arrow (from `orientation`), plot boundary, dimension lines for each room, and a distinct visual treatment (e.g., red hatching or outline) for any room currently carrying a soft violation — hard-violation plans are never rendered as "final" (§21.3), but a **draft/diagnostic render mode** may show violations explicitly during development/debugging.
- **PNG export** as a secondary, deterministic rasterization of the SVG (for convenience/sharing), not a separate generation path.
- **Furniture** rendering is optional (NICE-HAVE) — simple placeholder blocks (bed, sink, stove) placed via a lightweight per-room-type furniture-fitting heuristic, purely illustrative, not load-bearing on validation.
- Every rendered output includes the required disclaimer text (§26.8/NFR-8): "Conceptual layout — requires review by a licensed architect/engineer before construction."

---

## 26. Evaluation Metrics

Floor-plan quality is **not** a single-number problem. The framework below assigns the right metric family to the right sub-problem (§34 correction), and treats hard-constraint satisfaction as a gate, not an average-able input.

**A. Requirement Satisfaction** — % of explicit Priority-0 user requirements (bedroom/bathroom counts, named rooms, plot constraints) present and correctly typed/sized in the final plan.

**B. Room Classification** — for the vision baseline and for room-type assignment correctness: Accuracy, Precision, Recall, F1, confusion matrix (predicted vs. ground-truth/expected room type).

**C. Geometry** — MSE/MAE between predicted and reference (synthetic ground truth or CubiCasa5K-derived) room width, length, area, and coordinates.

**D. Spatial Similarity** — IoU of room polygons against reference, room-boundary similarity, corner error, wall-position error, door/window placement error.

**E. Graph Metrics** — adjacency accuracy (precision/recall of predicted adjacency edges vs. reference/required), connectivity accuracy (is every room reachable from the entrance), graph edit distance between predicted and reference adjacency graphs.

**F. Constraint Metrics** — hard-violation rate (must trend to zero for delivered plans), soft-violation rate, count of invalid/overlapping rooms, overlap percentage (summed overlapping area / total plan area), unreachable-room percentage.

**G. Architectural Quality Score** — sub-scores for ventilation, lighting, privacy, circulation, functionality, plumbing efficiency, space utilization, each computed from explicit, documented formulas (e.g., ventilation score = fraction of habitable rooms meeting the opening-to-floor-area ratio rule) — not learned/opaque scores, so they remain auditable.

**H. Modification Quality** (for the editing pipeline specifically) — did the parsed `EditIntent` match the human-annotated intended operation (synthetic test set with labeled expected edits); did the correct room(s) change; what fraction of *unaffected* rooms remained geometrically unchanged (preservation rate); did previously-satisfied Priority-0/1 requirements remain satisfied post-edit; disruption magnitude (§24.5) relative to a "necessary minimum" baseline for that edit type.

### 26.7 Composite Final Score

```
Final Score =
    RequirementSatisfaction
  × ArchitecturalValidity     (fraction of soft/functional rules satisfied)
  × GeometryQuality           (1 − normalized geometry error)
  × Connectivity
  × Ventilation
  × Lighting
  × Circulation
  × ModificationQuality        (only meaningful/reported for edit turns)
  [× VastuScore, reported separately, never multiplied into the gated score]
```

**Hard constraints are reported and gated separately** (`hard_violations == 0` required for a plan to be labeled "final/valid") specifically so that a high composite average can never mask a critical (e.g., overlapping rooms, missing egress) violation — this is the explicit correction required in §34 of the brief and is treated as a hard project requirement, not a suggestion.

---

## 27. Baselines

| Baseline | Description | Purpose |
|---|---|---|
| **B0 — Vision parsing baseline** | CubiCasa5K image → structured plan (§18), no NL input | Sanity-checks schema expressiveness; not compared on requirement satisfaction (no NL involved) |
| **B1 — Rule-based generator** | Deterministic room-program + slicing-tree geometry from requirement fields, *no LLM, no RAG* (fixed hard-coded rule table) | Isolates the value added by RAG + LLM reasoning over a purely deterministic system |
| **B2 — LLM-only structured generation** | LLM directly asked to emit the full structured plan JSON from the NL request, no retrieval, no deterministic validator | Demonstrates the hallucination/violation risk of unconstrained LLM generation (expected: high requirement-satisfaction on paper, high hard-violation rate on measurement) |
| **B3 — LLM + RAG** | B2 + retrieved rules injected into the prompt, still no deterministic geometry/validator | Demonstrates that retrieval alone reduces but does not eliminate constraint violations |
| **B4 — LLM + RAG + constraint solver** | B3's output geometry passed through the deterministic Constraint Validator (but with LLM-predicted coordinates, not solver-generated ones) and rejected/flagged on failure without repair | Demonstrates that validation catches violations but LLM-predicted geometry still needs a *generator*, not just a *checker* |
| **Final — Full Agentic System** | Full pipeline per §20: LLM for extraction/interpretation/explanation only; deterministic room-program checking, graph construction, slicing-tree geometry, constraint validation, and optimization/repair | Expected best on hard-violation rate (→0), competitive-to-best on requirement satisfaction, and uniquely capable on Modification Quality (H) since B0–B4 have no persistent-state editing pipeline at all |

**Expected result pattern:** requirement-satisfaction scores likely cluster fairly close across B2–Final (LLMs are generally good at *stating* they included the right rooms), while **hard-violation rate is expected to separate the baselines sharply** — this is the paper's central empirical claim: deterministic geometry + validation, not bigger/better prompting, is what actually produces valid plans. RNN vs. Transformer (§17) is reported as a narrow, secondary comparison, not a headline result.

---

## 28. Testing Strategy

- **Unit tests** per module: schema validators (RequirementObject, Rule, RoomProgram, GeometricPlan), geometry primitives (overlap detection, area computation, containment-in-plot), each Constraint Engine rule check (one test per rule category, with a known-pass and known-fail fixture plan).
- **Golden-plan regression tests:** a small hand-authored set of known-valid and known-invalid structured plans, checked into the notebook's fixtures, used to catch regressions in the Constraint Engine across changes.
- **Property-based tests** for the geometry generator: for N randomized `RoomProgram` inputs within supported ranges, assert the generator always returns non-overlapping, plot-contained geometry (even if some soft/hard rule violations remain, the *geometric* invariants must never fail).
- **End-to-end scenario tests:** the two demo scenarios in §31, executed as automated notebook assertions (expected room count, expected hard-violation count = 0, expected preserved-room set after each edit).
- **Modification-preservation tests:** for each supported edit operation (§24.3), assert that rooms outside the affected subgraph are byte-for-byte unchanged in the resulting `GeometricPlan`.
- **Infeasibility tests:** deliberately over-constrained requirement sets (e.g., 3 bathrooms + 2 bedrooms on a 300 sq ft plot) must produce an explicit infeasibility report, never a "successful" plan with hidden hard violations.
- **RAG evaluation:** retrieval precision/recall against a small hand-labeled query→expected-rule-ids set, to catch silent retrieval degradation.

---

## 29. Failure Handling

| Case | Detection | Resolution | User Communication |
|---|---|---|---|
| 1. Insufficient information | Blocking fields missing in `RequirementObject` | Ask minimal targeted clarification question(s) | "I need your plot's approximate width and length (or shape) to proceed." |
| 2. Impossible dimensions (e.g., 50 sq ft "bedroom") | Requirement-stage sanity check against Priority-1/2 minimums | Flag immediately, do not attempt generation | Explain the minimum and ask for a corrected value or plot size |
| 3. Too many rooms requested for plot size | CP-SAT feasibility pre-check (§23.2) before full geometry generation | Report infeasibility with the specific area shortfall; propose smallest plot increase or room-count reduction | "Your requested rooms need ~X sq ft; your plot supports ~Y sq ft. Consider removing one room or increasing plot size." |
| 4. Conflicting requirements (e.g., "no kitchen but has a stove room") | Requirement-schema cross-field validation | Ask a disambiguating question rather than guessing | Present the conflict plainly |
| 5. No valid layout exists (solver proves infeasible) | CP-SAT / repeated optimization failure with zero-violation target unreachable | Return the CP solver's minimal-conflict explanation | Explicit "not feasible as specified" message + smallest suggested change |
| 6. Vastu conflicts with architectural requirements | Vastu score computed separately; flagged when a Vastu-preferred placement would violate a Priority 0–4 rule | Priority 0–4 always wins; Vastu suggestion is shown as "not applied due to conflict with X" | Clearly labeled: "This Vastu preference could not be applied without violating [rule]." |
| 7. Local building rules conflict with generic/national rules | Rule re-ranker detects same `applies_to`+`constraint_type` with differing `jurisdiction` specificity | Higher-specificity jurisdiction rule wins deterministically | Logged in explanation: "Used [city] bye-law in place of national default." |
| 8. User edit causes new violations | Full-plan re-validation after every edit (§24.2) | Attempt scoped repair first, then expanded-scope repair if needed; if unrepairable, revert to pre-edit plan version and report why | "That change would leave [room] below minimum size; I couldn't resize without shrinking [other room] — here are the options." |
| 9. RAG retrieves conflicting information | Same as Case 7, or same rule from two unverified sources | Priority + verified-status + specificity ranking; if still tied, prefer the `national_code`/`source_type` with higher authority tier per §33 sourcing hierarchy | Disclosed if the conflict was not cleanly resolvable |
| 10. Generated geometry contains overlaps | Constraint Validator overlap check (should be structurally prevented by the slicing-tree generator, but checked regardless as a safety net) | Trigger repair loop immediately; this should be treated as a generator bug if it occurs, logged for debugging | Not surfaced to the user unless repair fails, in which case treated as Case 5 |

---

## 30. Notebook Structure

```
01_Project_Setup                  – environment, dependencies, Colab checks
02_Configuration                  – rule weights, jurisdiction defaults, model config
03_Dataset_Inspection              – CubiCasa5K / Structured3D / RPLAN-style exploration
04_Dataset_Preprocessing           – adapters: raw source -> unified schema (§13.5)
05_Unified_Dataset                 – assembled multi-source dataset object
06_Floorplan_Representation        – schema classes: RequirementObject, Rule, RoomProgram,
                                      AdjacencyGraph, GeometricPlan, ValidationReport
07_Rule_Engine                     – priority hierarchy implementation, hard/soft/preference logic
08_Knowledge_Base                  – curated Rule table (NBC/Model Bye-Laws/practice/Vastu excerpts)
09_Embedding_Model                 – embedding model setup for RAG
10_Vector_Database                 – FAISS/Chroma index build over the Knowledge Base
11_RAG                             – retrieval + re-ranking + rule-set assembly
12_Requirement_Extraction          – Requirement Agent (LLM, structured output)
13_LLM_Architecture                – model/provider config, structured-output enforcement
14_Room_Program_Generation         – Planning Agent (room list drafting + rule-checking)
15_Adjacency_Graph                 – zoning + graph construction, scored candidate search
16_Geometric_Generator             – slicing-tree layout, door/window placement
17_Constraint_Validator            – deterministic rule checks -> ValidationReport
18_Optimization                    – local search / annealing / CP-SAT repair
19_RNN_Baseline                    – §17 experiment (LSTM/GRU on room-sequence task)
20_Transformer_Baseline            – §17 comparison model
21_Floorplan_Renderer              – SVG generation + PNG export
22_Agentic_Workflow                – Orchestrator wiring all agents per §20 pipeline
23_Interactive_Modification        – Modification Agent + edit pipeline (§24)
24_Evaluation                      – metrics A–H (§26) computed over test scenarios
25_Visualization                   – evaluation charts, confusion matrices, score dashboards
26_Error_Analysis                  – failure-case walkthroughs (§29 cases reproduced)
27_Final_Demo                      – §31 end-to-end scenario, run live
```

Each numbered notebook section follows: **Explanation (markdown) → Code → Example Input → Example Output → Test cell → Visualization (where applicable)**, per the engineering requirement in the brief; no single monolithic cell.

---

## 31. Technology Stack

- **Language/runtime:** Python 3, Jupyter/Colab.
- **LLM access:** hosted API (e.g., Claude/GPT-class model via API) for tasks A–D/H in §16.1, with local open-weight fallback documented for offline/cost-constrained runs.
- **Structured-output enforcement:** JSON-schema-constrained decoding or strict prompt+validate+retry.
- **Embeddings/RAG:** sentence-transformer-class embedding model; FAISS or Chroma vector store.
- **Geometry:** `shapely` (polygon/overlap/containment operations), custom slicing-tree implementation.
- **Optimization:** local search implemented in plain Python; `OR-Tools` CP-SAT for feasibility proofs/minimal-conflict extraction.
- **Graph:** `networkx` for adjacency-graph representation and reachability/connectivity checks.
- **Vision baseline:** `PyTorch`/`torchvision` (or a lightweight segmentation library) for the CubiCasa5K-based room/wall/symbol detectors.
- **Rendering:** `svgwrite` (or direct SVG string templating) for vector output; `cairosvg`/`Pillow` for PNG export.
- **Evaluation:** `scikit-learn` (classification metrics), `numpy` (MSE/MAE), custom geometry-metric functions.

---

## 32. Computational Requirements

- **Deterministic pipeline** (requirement→geometry→validation→render): CPU-only, seconds per plan; no GPU required.
- **RAG:** embedding + retrieval over a knowledge base of a few thousand rule chunks — CPU-feasible, sub-second retrieval.
- **LLM calls:** dominant latency/cost driver; a full generation turn should require on the order of 3–6 LLM calls (extraction, room-program drafting, explanation, plus retrieval-query formulation); an edit turn should require 1–2 (intent parsing, diff explanation).
- **Vision baseline training** (segmentation/detection on a CubiCasa5K subset): feasible on a single Colab GPU (e.g., a small U-Net/YOLO-class model fine-tuned for a few epochs on a subset, not the full 5K set, to stay within free/standard Colab session limits).
- **RNN/Transformer sequence experiment (§17):** small models, trivially feasible on Colab CPU or a single GPU in minutes.
- Explicitly **not required:** multi-GPU training, distributed training, foundation-model pretraining, or training runs exceeding a single Colab session.

---

## 33. Expected Results

- Hard-violation rate should trend to **zero for delivered ("final") plans** in the Full Agentic System, by construction of the gating rule in §21.3/§26.7 — this is a design guarantee, not merely an empirical hope, and should be reflected in evaluation (any residual nonzero rate indicates a generator/validator bug to be found via the golden-plan regression tests, §28).
- B1 (rule-based, no LLM) is expected to also achieve low hard-violation rates but score **lower on Requirement Satisfaction** for less common/compound requests (e.g., pooja room + study room combinations it wasn't explicitly coded for), since it lacks the LLM's ability to interpret novel phrasing into the existing schema.
- B2/B3 (LLM-only / LLM+RAG without deterministic geometry) are expected to show the **highest hard-violation rates**, evidencing the core thesis that retrieval and prompting reduce but do not eliminate constraint violations without a deterministic validator+generator.
- The Full Agentic System is expected to be the **only** baseline with non-trivial Modification Quality (H) scores, since B0–B4 have no persistent, scoped-editing pipeline.
- RNN vs. Transformer (§17): expected roughly comparable next-room accuracy on common layouts, with the Transformer/LLM expected to generalize better to less-common room combinations, per the reasoning in §17 — reported as a secondary, exploratory finding.

---

## 34. Demo Scenarios

See the fully worked example in §31 of this document's structure — reproduced in full detail below as the canonical end-to-end scenario, matching the brief's required demo flow.

---

## 35. Limitations

- Coverage of local/municipal bye-laws is necessarily partial in the prototype; most jurisdictions fall back to Model Bye-Law/NBC defaults with an explicit "not jurisdiction-verified" flag rather than a false claim of local compliance.
- The synthetic dataset, while schema-complete, may not fully capture the diversity of real user phrasing or real site irregularities (non-rectangular plots, extreme aspect ratios); irregular-plot support is scoped as SHOULD/NICE-HAVE (§37).
- Multi-floor support (staircase placement, vertical service stacking) is limited in the initial prototype.
- The vision component (§18) is trained on non-Indian floor plans (CubiCasa5K is Finnish); its structure-recovery accuracy on Indian-style plans is not guaranteed and is explicitly an evaluation question, not an assumption.
- Furniture placement, if included, is illustrative only and not validated against ergonomic clearance rules in the MUST-HAVE scope.
- The system produces conceptual, non-certified output; it cannot and does not replace structural engineering, licensed architectural review, or formal statutory approval processes.

---

## 36. Future Scope

- GNN-based adjacency-graph scoring/completion (§19), once sufficient labeled graph data exists (bootstrappable from the synthetic generator's outputs over time).
- Fine-tuning (e.g., LoRA) of the extraction/interpretation LLM on accumulated synthetic + (anonymized, consented) real usage data, if structured-prompting accuracy proves insufficient.
- Expanded, verified local/municipal bye-law coverage across more Indian jurisdictions, with a formal human-review/sign-off workflow for marking a rule "verified."
- Full multi-floor design (staircases, vertical plumbing stacks, floor-to-floor structural continuity checks).
- Irregular/non-rectangular plot support in the geometry generator (beyond slicing-tree rectangular partitioning — e.g., polygon-clipping-based partitioning).
- Image-upload-driven editing: user uploads an existing plan photo/scan, the vision pipeline (§18) parses it into a structured plan, and it enters the same conversational-edit pipeline as an AI-generated plan.
- Learned weight-tuning for the composite scoring function (§23.3) from human pairwise preference data.
- 3D massing/visualization as an optional additional rendering mode (still derived from the same structured source of truth).
- RL-based exploration of the geometry search space if evaluation later shows the deterministic search plateauing on plan diversity/quality for complex requirement sets.

---

## 37. Development Roadmap (MUST / SHOULD / NICE / FUTURE)

**MUST HAVE (required working prototype):**
Requirement extraction + clarification; single-floor, rectangular-plot geometry generation via slicing-tree; full Priority 0–4 rule hierarchy with NBC/Model Bye-Law-sourced Priority-1 rules (defaulted where jurisdiction unverified); deterministic Constraint Validator (all categories in §21.1); local-search + CP-SAT-backed repair/infeasibility detection; SVG rendering with all required elements (§25); grounded explanation generation; the full MUST-HAVE edit-operation set (§24.3) with scoped generation + full-plan re-validation; the synthetic dataset generator (§13.4/§29 of source brief); the full evaluation framework (§26 A–H) run against synthetic test scenarios; the B1–Final baseline ladder (§27, B0 optional at MUST-HAVE); notebook structure per §30.

**SHOULD HAVE:**
Vastu preference layer with separate scoring; jurisdiction-aware rule re-ranking with a small set of real municipal bye-law excerpts beyond the national default; extended edit-operation set (add balcony/parking/staircase, change entrance/orientation — single added element, still single-floor); vision-baseline (§18) trained on a CubiCasa5K subset for structure-recovery evaluation; furniture-placement illustrative rendering; light LoRA fine-tuning of the extraction model if evaluation warrants it (§16.2).

**NICE TO HAVE:**
RNN vs. Transformer sequence experiment (§17) as a reported academic artifact; PNG export polish/legend refinement; image-upload → structured-plan editing entry point (full pipeline, not just the parser); multi-floor support (add/remove floor edits, staircase placement); irregular-plot geometry support.

**FUTURE WORK (explicitly not implemented initially):**
GNN-based graph scoring; RL-based geometry search; full multi-jurisdiction verified bye-law database; 3D visualization; learned composite-score weight tuning from human preference data; production-grade multi-user/multi-session deployment (this PRD scopes a research/demo notebook, not a hosted product).

---

## 38. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM hallucinates a building regulation not actually in the Knowledge Base | Medium | High (credibility/safety) | Hard architectural boundary: retrieved-and-verified `Rule` objects only feed the Constraint Engine; LLM explanations are grounded/templated from `ValidationReport` + cited `rule_id`s, never freely asserting numeric code values (§15.4, §26) |
| Local bye-laws misrepresented as universal | Medium | High | Explicit `jurisdiction` field + "not jurisdiction-verified" flag on every non-locally-confirmed Priority-1 rule (§13.3, §35) |
| Geometry generator produces overlapping/invalid rooms despite the validator | Low (mitigated by slicing-tree's overlap-by-construction guarantee) | Medium | Overlap check retained as a safety net (§29 Case 10); property-based tests (§28) |
| Structured-output LLM calls return malformed JSON | Medium | Medium | Schema-constrained decoding + automatic re-ask/retry with validation error fed back to the model |
| Synthetic training/eval data doesn't reflect real user phrasing diversity | Medium | Medium | Paraphrase augmentation in the synthetic generator; evaluation explicitly reports this as a limitation (§35), not hidden |
| Scope creep toward "maximum AI techniques used" rather than correctness | Medium | Medium | §7's explicit non-goal, RNN/GNN/RL sections each end with a justified "not used / future work" disposition rather than forced inclusion |
| Vastu preference accidentally overriding safety/legal rules | Low (by design) | High if it occurred | Vastu scored strictly separately and gated below Priority 0–4 in code, not just in documentation (§21.3, §29 Case 6) |
| CP-SAT / optimization runtime blow-up on larger requirement sets | Low at prototype scale (small room counts) | Low–Medium | Scope limited to typical residential room counts (5–15); timeout + fallback-to-heuristic-repair if solver exceeds a time budget |

---

## 39. Acceptance Criteria

The prototype is considered to meet MUST-HAVE acceptance when, on the notebook's own synthetic test scenario set:

1. **AC-1:** For all "feasible" synthetic test requirements, the Full Agentic System returns a final plan with `hard_violations == 0`.
2. **AC-2:** For all "infeasible-by-design" synthetic test requirements, the system returns an explicit infeasibility report (not a plan with hidden hard violations, and not a bare failure with no explanation).
3. **AC-3:** Requirement Satisfaction (metric A, §26) ≥ a documented threshold (e.g., ≥95%) across the feasible test set.
4. **AC-4:** For every supported edit operation (§24.3), the Modification-Preservation test (§28) passes: rooms outside the affected subgraph are unchanged.
5. **AC-5:** Every rendered final plan includes all required elements from §25 and the required disclaimer text.
6. **AC-6:** Every hard-violation and every automatic repair in the log is traceable to a specific `rule_id` (NFR-4 auditability).
7. **AC-7:** The baseline ladder (§27) is fully implemented and evaluated, with results reported (not merely described) in the notebook's `24_Evaluation`/`25_Visualization` sections.
8. **AC-8:** The complete notebook runs top-to-bottom on a fresh Colab runtime without manual intervention (NFR-2).
9. **AC-9:** The §31/§34 canonical demo scenario (below) executes successfully end-to-end within the notebook's `27_Final_Demo` section.

---

## 40. Full End-to-End Demo Scenario (Canonical)

**Turn 1 — Initial generation**

> **User:** "I have a 1000 sq ft plot. I want a 2BHK with one attached bathroom, one common bathroom, kitchen, dining, living room and good natural ventilation."

Pipeline trace:
`User Input → RequirementObject {bedrooms:2, bathrooms:{attached:1, common:1}, must_have:[kitchen,dining,living_room], plot_area:1000, preferences:{ventilation:"good"}} → Retrieved Rules (NBC habitable-room minimums, ventilation opening ratio, bathroom minimums, functional adjacency rules for kitchen–dining, living–entrance) → Room Program (7 rooms with target areas summing within plot/footprint limits) → Adjacency Graph (entrance–living–dining–kitchen cluster; bedroom_1+attached_bath cluster; bedroom_2; common_bath reachable without crossing bedrooms) → Generated Geometry (slicing-tree partition into public/private/service zones, room polygons, doors, windows) → Validation (hard_violations: 0 after one repair pass adjusting bedroom_2 width) → Optimization (soft-violation count reduced from 2 to 0 via local search) → Final Plan (v1) → 2D Rendering (SVG with labels, dimensions, north arrow, legend) → Evaluation Score (Requirement Satisfaction 100%, Architectural Validity 100%, Ventilation score high due to cross-ventilated bedrooms)`.

**Turn 2 — Add a room near the entrance**

> **User:** "Add a pooja room near the entrance."

Pipeline trace:
`Existing Plan (v1) → EditIntent {operation:"add", target:"pooja_room", constraints:["near entrance"]} → Candidate Locations generated from available residual space adjacent to the entrance/living zone → Candidate Scoring (§25 function: space availability, adjacency to entrance, low circulation disruption, acceptable lighting) → Selected Location (small alcove off the living room, entrance-adjacent) → Modified Geometry (only living-room boundary and the new pooja-room polygon change; kitchen/bedrooms/bathrooms untouched) → Re-validation (full-plan check: hard_violations 0; living room area re-checked against its minimum after the boundary adjustment) → Updated Plan (v2) → Diff Explanation ("Added a pooja room adjacent to the entrance/living area; living room resized from 180 sq ft to 165 sq ft, still above the functional minimum; all other rooms unchanged.")`.

**Turn 3 — Constrained resize**

> **User:** "Make the master bedroom larger but don't reduce the kitchen."

Pipeline trace:
`Existing Plan (v2) → EditIntent {operation:"resize", target:"bedroom_1", direction:"increase", constraints:["kitchen area must not decrease"]} → Affected-Subgraph Extraction (bedroom_1 and its immediately adjacent slack-space neighbor, excluding kitchen from the candidate resize pool) → Candidate Generation (search for adjacent zone with reclaimable slack — e.g., circulation buffer or bedroom_2's margin — respecting the "don't touch kitchen" hard constraint injected for this turn) → Candidate Scoring → Selected Candidate (bedroom_1 enlarged by reclaiming circulation buffer margin) → Constraint Engine (confirms kitchen area unchanged; confirms bedroom_2 and circulation width still meet minimums) → Updated Plan (v3) → Explanation ("Master bedroom increased from 132 sq ft to 150 sq ft by reclaiming circulation margin; kitchen area unchanged at 80 sq ft as requested; bedroom_2 and common-bath access unaffected.")`.

This scenario is implemented as an executable, asserted sequence in `27_Final_Demo`, satisfying AC-9.

---

*End of PRD.*
