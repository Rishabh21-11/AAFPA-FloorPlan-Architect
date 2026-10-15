"""
AAFPA 2.0 — Condition-Grounded Smart Conversational Architectural Agent
========================================================================
The central intelligence and orchestration layer for AAFPA.

Principle:
    USER_UTTERANCE + CURRENT_PLAN_STATE + CONVERSATION_HISTORY
    -> Diagnose spatial conditions
    -> Ground intent in real plan topology & discourse memory
    -> Extract preservation & environmental constraints
    -> Evaluate geometric feasibility (zero hallucination)
    -> Emit structured ArchitecturalOperation / Engine Orders
    -> Two-phase commit protocol: execute -> validate -> confirm or explain failure
"""

import re
import copy
import math
from typing import Optional, List, Dict, Any, Tuple

from aafpa.ontology import (
    ArchitecturalOntology,
    SYNONYM_TO_CANONICAL,
    CANONICAL_ROOM_TYPES,
    TAXONOMY_INTENT_FAMILIES
)
from aafpa.actions import (
    ArchitecturalActionType,
    ArchitecturalOperation,
    DimensionSpec,
    StructuredArchitecturalIntent
)
from aafpa.spatial_reasoning import SpatialReasoningEngine

# ---------------------------------------------------------------------------
# Condition thresholds (tunable)
# ---------------------------------------------------------------------------
CORRIDOR_EXCESS_RATIO = 0.10   # corridors exceeding 10% of total area => spaciousness candidate
LIVING_COMPARTMENT_RATIO = 0.6 # living-to-dining shared_wall/perimeter below 60% => open concept
ASPECT_RATIO_THRESHOLD = 2.0   # width/length > 2 => geometric imbalance
MIN_ROOM_AREA_PRIVACY = 90.0   # master bedroom < 90 sqft => privacy concern

# ---------------------------------------------------------------------------
# High-level goal vocabulary
# ---------------------------------------------------------------------------
SPACIOUSNESS_TRIGGERS = [
    "more spacious", "feel bigger", "feel larger", "open up", "less cramped",
    "more open", "open feel", "breathing space", "airy", "open concept",
    "reduce wasted space", "less wasted", "efficient layout", "feel cramped"
]
PRIVACY_TRIGGERS = [
    "more private", "improve privacy", "better privacy", "seclude", "more quiet",
    "make it quiet", "separate bedrooms", "less visible", "privacy for bedroom",
    "feel too exposed", "too exposed", "more peaceful", "make this layout more private"
]
VENTILATION_TRIGGERS = [
    "ventilation", "airflow", "breeze", "cross ventilation", "air circulation",
    "well ventilated", "more air", "fresh air", "natural ventilation", "cross-ventilation"
]
LIGHTING_TRIGGERS = [
    "natural light", "more light", "brighter", "sunlight", "daylight",
    "better lighting", "well lit", "less dark", "too dark", "more windows"
]
CIRCULATION_TRIGGERS = [
    "circulation", "movement", "flow", "connectivity", "accessibility",
    "better access", "easier to move", "reduce bottleneck", "less congested"
]


class DiscourseEntity:
    """A room reference tracked across conversational turns."""
    __slots__ = ("room_id", "room_type", "turn_index", "confidence")

    def __init__(self, room_id: Optional[str], room_type: Optional[str],
                 turn_index: int = 0, confidence: float = 1.0):
        self.room_id = room_id
        self.room_type = room_type
        self.turn_index = turn_index
        self.confidence = confidence

    def __repr__(self):
        return f"<Entity type={self.room_type} id={self.room_id} turn={self.turn_index}>"


class PlanConditionReport:
    """
    Structural analysis of the active floor plan state.
    Used to ground high-level goals into concrete geometric operations.
    """

    def __init__(self):
        self.corridor_ratio: float = 0.0
        self.has_excess_corridor: bool = False
        self.living_dining_wall_shared: bool = False
        self.compartmentalized_public: bool = False
        self.poor_aspect_rooms: List[str] = []
        self.bedrooms_near_entrance: List[str] = []
        self.rooms_without_windows: List[str] = []
        self.smallest_bedroom_area: float = float("inf")
        self.largest_room: Optional[str] = None
        self.total_built_up: float = 0.0
        self.room_count: int = 0
        self.candidate_spaciousness_actions: List[str] = []
        self.candidate_privacy_actions: List[str] = []
        self.candidate_ventilation_actions: List[str] = []

    def to_summary(self) -> str:
        lines = [
            f"Total built-up: {self.total_built_up:.0f} sqft | Rooms: {self.room_count}",
            f"Corridor ratio: {self.corridor_ratio:.1%} | Excess: {self.has_excess_corridor}",
            f"Compartmentalized public zone: {self.compartmentalized_public}",
            f"Poor aspect ratio rooms: {self.poor_aspect_rooms}",
            f"Rooms without windows: {self.rooms_without_windows}",
            f"Smallest bedroom: {self.smallest_bedroom_area:.0f} sqft",
        ]
        return " | ".join(lines)


class ConditionGroundedSmartAgent:
    """
    Condition-grounded conversational architectural intelligence.
    Extracts intents, resolves pronouns, handles preservation constraints,
    diagnoses plan geometry, and outputs structured engine orders.
    """

    def __init__(self, memory=None):
        from aafpa.semantic_agent import PlanMemory
        self.memory = memory if memory is not None else PlanMemory()
        self.ontology = ArchitecturalOntology()
        self._turn_index: int = 0
        self._entity_stack: List[DiscourseEntity] = []
        self._conversation_history: List[Dict[str, str]] = []
        self._active_preservations: List[str] = []

    def parse_intent(self, text: str,
                     current_plan: Optional[Any] = None) -> StructuredArchitecturalIntent:
        """
        Primary entry point.
        Analyzes the user's utterance against current plan state and conversation history.
        """
        self._turn_index += 1
        t = text.strip()
        t_lower = t.lower()
        plan = current_plan or (self.memory.current_plan if self.memory else None)

        self._conversation_history.append({"role": "user", "text": t})

        # ------------------------------------------------------------------
        # Stage 0: Meta commands (Undo, Redo, Layout Selection, Finalize)
        # ------------------------------------------------------------------
        meta = self._check_meta_commands(t_lower, t)
        if meta:
            return meta

        # ------------------------------------------------------------------
        # Stage 1: Check Infeasibility / Impossible Physical Requests
        # ------------------------------------------------------------------
        infeasible = self._check_infeasibility(t_lower, t, plan)
        if infeasible:
            return infeasible

        # ------------------------------------------------------------------
        # Stage 2: Conversational / Informational / RAG QA Questions
        # ------------------------------------------------------------------
        conversational = self._check_conversational_qa(t_lower, t, plan)
        if conversational:
            return conversational

        # ------------------------------------------------------------------
        # Stage 3: Diagnose Current Plan Conditions
        # ------------------------------------------------------------------
        condition_report = self._diagnose_plan(plan)

        # ------------------------------------------------------------------
        # Stage 4: Extract Preservation Constraints ("don't touch X")
        # ------------------------------------------------------------------
        preserve_rooms = self._extract_preservation_constraints(t_lower, plan)
        if preserve_rooms:
            for p in preserve_rooms:
                if p not in self._active_preservations:
                    self._active_preservations.append(p)

        # ------------------------------------------------------------------
        # Stage 5: High-Level Goal Resolution (Spacious, Ventilation, Privacy)
        # ------------------------------------------------------------------
        high_level = self._detect_high_level_goal(t_lower)
        if high_level:
            intent = self._resolve_high_level_goal(
                high_level, t, plan, condition_report
            )
            intent.preserve_rooms = list(self._active_preservations)
            return intent

        # ------------------------------------------------------------------
        # Stage 6: Entity Resolution (Pronouns, Context, Adjacencies)
        # ------------------------------------------------------------------
        target_rtype, target_rid = self._resolve_target_room(t_lower, plan)

        # ------------------------------------------------------------------
        # Stage 7: Classify Atomic / Compound Architectural Operations
        # ------------------------------------------------------------------
        operations, clarification_q = self._classify_atomic_operation(
            t, t_lower, plan, target_rtype, target_rid, condition_report
        )

        if clarification_q:
            return StructuredArchitecturalIntent(
                intent_category="clarification",
                message_type="clarification",
                clarification_needed=True,
                clarification_question=clarification_q,
                raw_prompt=t,
            )

        # Update entity memory stack with the operational target
        if operations:
            for op in operations:
                if op.type == ArchitecturalActionType.ADD_ROOM and op.target_room:
                    self._push_entity(None, op.target_room)
                elif op.type == ArchitecturalActionType.REPLACE_ROOM and op.source_room:
                    self._push_entity(op.target_id, op.source_room)
                elif op.target_room:
                    self._push_entity(op.target_id, op.target_room)
        elif target_rtype:
            self._push_entity(target_rid, target_rtype)

        # Attach preservation constraints to operations
        hard_constraints = [f"PRESERVE:{p}" for p in self._active_preservations]
        for op in operations:
            op.hard_constraints = list(hard_constraints)

        return StructuredArchitecturalIntent(
            intent_category="modify_layout",
            message_type="architectural_action",
            operations=operations,
            preserve_rooms=list(self._active_preservations),
            hard_constraints=hard_constraints,
            raw_prompt=t,
            resolved_references=self._current_entity_dict(),
        )

    # =======================================================================
    # Stage 0: Meta commands
    # =======================================================================
    def _check_meta_commands(self, t_lower: str, t: str) -> Optional[StructuredArchitecturalIntent]:
        # Layout selection
        m_sel = re.search(r'\b(?:select|choose|pick|activate|layout|option)\s*#?\s*([1-4])\b', t_lower)
        if not m_sel and re.match(r'^[1-4]$', t_lower.strip()):
            m_sel = re.match(r'^([1-4])$', t_lower.strip())
        if m_sel:
            opt_num = int(m_sel.group(1))
            return StructuredArchitecturalIntent(
                intent_category="select_layout",
                message_type="architectural_action",
                operations=[ArchitecturalOperation(
                    type=ArchitecturalActionType.SELECT_LAYOUT,
                    parameters={"option_number": opt_num}
                )],
                raw_prompt=t,
            )

        # Undo / Revert
        if any(w in t_lower for w in ["undo", "revert", "go back", "previous version", "step back"]):
            return StructuredArchitecturalIntent(
                intent_category="undo",
                message_type="undo",
                operations=[ArchitecturalOperation(type=ArchitecturalActionType.UNDO)],
                raw_prompt=t,
            )

        # Redo
        if any(w in t_lower for w in ["redo", "step forward"]):
            return StructuredArchitecturalIntent(
                intent_category="redo",
                message_type="redo",
                operations=[ArchitecturalOperation(type=ArchitecturalActionType.REDO)],
                raw_prompt=t,
            )

        # Finalize
        if any(w in t_lower for w in ["finalize", "lock plan", "done editing", "approve plan"]):
            return StructuredArchitecturalIntent(
                intent_category="finalize_plan",
                message_type="conversation",
                operations=[ArchitecturalOperation(type=ArchitecturalActionType.FINALIZE_PLAN)],
                raw_prompt=t,
            )

        return None

    # =======================================================================
    # Stage 1: Infeasibility & Physical Bound Checks
    # =======================================================================
    def _check_infeasibility(self, t_lower: str, t: str, plan: Optional[Any]) -> Optional[StructuredArchitecturalIntent]:
        """Detects impossible spatial requests before engine execution."""
        # 5+ bedrooms in tiny plot
        m_bed = re.search(r'(\d+)\s*(?:bed|bedroom|bhk)', t_lower)
        if m_bed:
            beds = int(m_bed.group(1))
            if beds >= 5 and any(sq in t_lower for sq in ["400", "500", "600"]):
                return StructuredArchitecturalIntent(
                    intent_category="infeasible",
                    message_type="infeasible",
                    raw_prompt=t,
                    clarification_needed=True,
                    clarification_question=(
                        f"It is physically impossible to fit {beds} bedrooms in under 600 sqft. "
                        "According to NBC standards, each bedroom requires at least 80 sqft plus circulation. "
                        "Would you like a 1BHK or 2BHK layout instead?"
                    )
                )

        # Absurd room dimensions (e.g. 50 ft wide in 32 ft plot)
        m_wide = re.search(r'(\d+)\s*(?:feet|ft|foot)\s*(?:wide|width|length|long)', t_lower)
        if m_wide:
            dim_val = float(m_wide.group(1))
            plot_w = getattr(getattr(plan, "plot", None), "width_ft", 32.0)
            if dim_val > plot_w + 10:
                return StructuredArchitecturalIntent(
                    intent_category="infeasible",
                    message_type="infeasible",
                    raw_prompt=t,
                    clarification_needed=True,
                    clarification_question=(
                        f"A dimension of {dim_val:.0f} feet exceeds your plot boundary ({plot_w:.0f} feet). "
                        f"The maximum allowable dimension along this axis is {plot_w - 4:.0f} feet."
                    )
                )

        return None

    # =======================================================================
    # Stage 2: Conversational / RAG QA / Explanations
    # =======================================================================
    def _check_conversational_qa(self, t_lower: str, t: str, plan: Optional[Any]) -> Optional[StructuredArchitecturalIntent]:
        """Handles greetings, architectural explanations, layout comparisons, and room dimension queries."""
        # Greeting
        if t_lower in ("hello", "hi", "hey", "good morning", "good evening"):
            return StructuredArchitecturalIntent(
                intent_category="conversation",
                message_type="conversation",
                raw_prompt=t,
            )

        # Room size standards question
        if "what is a good" in t_lower or "standard size" in t_lower or "recommended size" in t_lower:
            return StructuredArchitecturalIntent(
                intent_category="query_plan",
                message_type="question",
                raw_prompt=t,
            )

        # Layout comparison
        if "which" in t_lower and ("layout" in t_lower or "option" in t_lower):
            return StructuredArchitecturalIntent(
                intent_category="query_plan",
                message_type="comparison",
                raw_prompt=t,
            )

        # Explaining design decision
        if t_lower.startswith("why") or "why did you" in t_lower or "why is the" in t_lower:
            return StructuredArchitecturalIntent(
                intent_category="explain_plan",
                message_type="conversation",
                raw_prompt=t,
            )

        return None

    # =======================================================================
    # Stage 3: Plan condition diagnosis
    # =======================================================================
    def _diagnose_plan(self, plan: Optional[Any]) -> PlanConditionReport:
        report = PlanConditionReport()
        if plan is None or not hasattr(plan, "rooms"):
            return report

        rooms = plan.rooms
        report.room_count = len(rooms)
        total_area = sum(getattr(r, "area", r.width * r.length
                         if hasattr(r, "width") else 0) for r in rooms)
        report.total_built_up = total_area

        # Corridor ratio
        corridor_area = sum(
            getattr(r, "area", r.width * r.length) for r in rooms if "corridor" in r.type
        )
        report.corridor_ratio = corridor_area / max(total_area, 1.0)
        report.has_excess_corridor = report.corridor_ratio > CORRIDOR_EXCESS_RATIO

        # Compartmentalized public zone
        living = next((r for r in rooms if r.type == "living_room"), None)
        dining = next((r for r in rooms if r.type == "dining"), None)
        if living and dining:
            adj = SpatialReasoningEngine.get_adjacent_rooms(living, rooms)
            report.living_dining_wall_shared = any(r.id == dining.id for r in adj)
            report.compartmentalized_public = not report.living_dining_wall_shared

        # Poor aspect ratios
        for r in rooms:
            w = getattr(r, "width", 1.0)
            l = getattr(r, "length", 1.0)
            ratio = max(w, l) / max(min(w, l), 0.01)
            if ratio > ASPECT_RATIO_THRESHOLD and "corridor" not in r.type:
                report.poor_aspect_rooms.append(r.id)

        # Rooms without windows
        for r in rooms:
            wins = getattr(r, "windows", [])
            if len(wins) == 0 and r.type not in ("corridor", "foyer", "utility"):
                report.rooms_without_windows.append(r.id)

        return report

    # =======================================================================
    # Stage 4: Preservation Constraints
    # =======================================================================
    def _extract_preservation_constraints(self, t_lower: str, plan: Optional[Any]) -> List[str]:
        """Extracts room types that must not be altered during the edit."""
        preserve = []
        patterns = [
            r"(?:don'?t\s+touch|don'?t\s+change|don'?t\s+reduce|do\s+not\s+touch|do\s+not\s+change|do\s+not\s+reduce)\s+(?:the\s+)?([a-z0-9_\s]+)",
            r"(?:without\s+changing|without\s+reducing|without\s+altering|keep\s+intact|preserve)\s+(?:the\s+)?([a-z0-9_\s]+)",
            r"(?:keep|leave)\s+(?:the\s+)?([a-z0-9_\s]+?)\s+(?:as\s+is|unchanged|intact)",
        ]
        for pat in patterns:
            for m in re.finditer(pat, t_lower):
                phrase = m.group(1).strip()
                # If plural bedrooms
                if "bedroom" in phrase and "master" not in phrase:
                    preserve.extend(["bedroom", "master_bedroom"])
                else:
                    rtype = self.ontology.resolve_room_type(phrase)
                    if rtype and rtype not in preserve:
                        preserve.append(rtype)

        return preserve

    # =======================================================================
    # Stage 5: High-Level Goal Detection & Resolution
    # =======================================================================
    def _detect_high_level_goal(self, t_lower: str) -> Optional[str]:
        if any(w in t_lower for w in ["add ", "create ", "insert ", "build ", "put in "]):
            return None
        if any(w in t_lower for w in SPACIOUSNESS_TRIGGERS):
            return "spaciousness"
        if any(w in t_lower for w in PRIVACY_TRIGGERS):
            return "privacy"
        if any(w in t_lower for w in VENTILATION_TRIGGERS):
            return "ventilation"
        if any(w in t_lower for w in LIGHTING_TRIGGERS):
            return "lighting"
        if any(w in t_lower for w in CIRCULATION_TRIGGERS):
            return "circulation"
        return None

    def _resolve_high_level_goal(self, goal: str, text: str,
                                 plan: Optional[Any],
                                 report: PlanConditionReport) -> StructuredArchitecturalIntent:
        ops = []
        if goal == "spaciousness":
            if report.has_excess_corridor:
                ops.append(ArchitecturalOperation(
                    type=ArchitecturalActionType.TRANSFER_AREA,
                    source_room="corridor",
                    target_room="living_room",
                    dimension=DimensionSpec(value=25.0, unit="sqft", direction="increase")
                ))
            elif report.compartmentalized_public:
                ops.append(ArchitecturalOperation(type=ArchitecturalActionType.MAKE_OPEN_CONCEPT))
            else:
                ops.append(ArchitecturalOperation(
                    type=ArchitecturalActionType.RESIZE_ROOM,
                    target_room="living_room",
                    dimension=DimensionSpec(value=2.0, unit="ft", direction="increase")
                ))

        elif goal == "ventilation":
            ops.append(ArchitecturalOperation(
                type=ArchitecturalActionType.ADD_WINDOW_CROSS_VENT,
                target_room="living_room"
            ))

        elif goal == "privacy":
            ops.append(ArchitecturalOperation(
                type=ArchitecturalActionType.RELOCATE_DOOR_FOR_PRIVACY,
                target_room="master_bedroom"
            ))

        elif goal == "lighting":
            ops.append(ArchitecturalOperation(
                type=ArchitecturalActionType.INCREASE_WINDOW_SIZE,
                target_room="living_room"
            ))

        else:
            ops.append(ArchitecturalOperation(type=ArchitecturalActionType.IMPROVE_CIRCULATION))

        return StructuredArchitecturalIntent(
            intent_category="modify_layout",
            message_type="architectural_action",
            operations=ops,
            raw_prompt=text
        )

    # =======================================================================
    # Stage 6: Reference & Target Resolution
    # =======================================================================
    def _resolve_target_room(self, t_lower: str, plan: Optional[Any]) -> Tuple[Optional[str], Optional[str]]:
        # Pronoun resolution ("it", "that room", "the previous room")
        if re.search(r'\b(it|this|that|that room|the previous room|the same room)\b', t_lower):
            if self._entity_stack:
                top = self._entity_stack[-1]
                return top.room_type, top.room_id

        # "The one beside the kitchen" / spatial reference
        m_rel = re.search(r'the\s+(?:one|room)\s+(?:beside|next to|near|adjacent to)\s+(?:the\s+)?([a-z_]+)', t_lower)
        if m_rel and plan and hasattr(plan, "rooms"):
            anchor_type = self.ontology.resolve_room_type(m_rel.group(1))
            if anchor_type:
                anchor_room = next((r for r in plan.rooms if r.type == anchor_type), None)
                if anchor_room:
                    adj = SpatialReasoningEngine.get_adjacent_rooms(anchor_room, plan.rooms)
                    if adj:
                        return adj[0].type, adj[0].id

        # "The other bedroom" / "the smaller bedroom"
        if "other bedroom" in t_lower or "second bedroom" in t_lower:
            return "bedroom", "bed_2"
        if "smaller bedroom" in t_lower:
            return "bedroom", "bed_2"
        # Functional inference ("quiet place to work", "somewhere for prayer", "workout place")
        inferred = self.ontology.infer_functional_room_type(t_lower)
        if inferred:
            rid = None
            if plan and hasattr(plan, "rooms"):
                matching = [r for r in plan.rooms if r.type == inferred]
                if matching:
                    rid = matching[0].id
            return inferred, rid

        # Direct room extraction (excluding bare 'room')
        for syn, canonical in sorted(SYNONYM_TO_CANONICAL.items(),
                                      key=lambda x: len(x[0]), reverse=True):
            if syn == "room":
                continue
            pattern = r'\b' + re.escape(syn) + r'\b'
            if re.search(pattern, t_lower):
                # Match room ID in active plan if available
                rid = None
                if plan and hasattr(plan, "rooms"):
                    matching = [r for r in plan.rooms if r.type == canonical]
                    if matching:
                        rid = matching[0].id
                return canonical, rid

        return None, None

    # =======================================================================
    # Stage 7: Atomic Operation Classification
    # =======================================================================
    def _classify_atomic_operation(self, text: str, t_lower: str,
                                   plan: Optional[Any],
                                   target_rtype: Optional[str],
                                   target_rid: Optional[str],
                                   report: PlanConditionReport) -> Tuple[List[ArchitecturalOperation], Optional[str]]:
        ops = []
        val, unit, scale = self.ontology.parse_dimension_amount(text)

        # ---- AREA TRANSFER ----------------------------------------------
        if any(w in t_lower for w in ["give it to", "transfer", "take space from", "use some space from", "use some of the"]):
            src_type, src_id = self._extract_source_room(t_lower, plan)
            dst_type, dst_id = self._extract_destination_room(t_lower, plan)
            if not dst_type and target_rtype:
                dst_type, dst_id = target_rtype, target_rid
            if not src_type:
                src_type = "dining" if "dining" in t_lower else "corridor"

            ops.append(ArchitecturalOperation(
                type=ArchitecturalActionType.TRANSFER_AREA,
                source_room=src_type, source_id=src_id,
                target_room=dst_type or "living_room", target_id=dst_id,
                dimension=DimensionSpec(value=val or 20.0, unit=unit or "sqft", direction="increase")
            ))
            return ops, None

        # ---- ROOM ADDITION (Standard or Custom) -------------------------
        if any(w in t_lower for w in ["add", "create", "include", "put in", "build"]):
            added_type = self._extract_added_room_type(t_lower) or target_rtype
            if not added_type:
                added_type = self.ontology.infer_functional_room_type(t_lower) or "balcony"

            anchor = self._extract_anchor_room(t_lower, exclude_type=added_type)
            rel = self.ontology.resolve_spatial_relation(t_lower) or "beside"

            ops.append(ArchitecturalOperation(
                type=ArchitecturalActionType.ADD_ROOM,
                target_room=added_type,
                relative_target=anchor,
                spatial_relation=rel,
                dimension=DimensionSpec(value=val or 80.0, unit="sqft", direction="increase")
            ))
            return ops, None

        # ---- ROOM REPLACEMENT / CONVERSION ------------------------------
        if any(w in t_lower for w in ["replace", "convert", "turn", "transform", "substitute"]) or (
            any(w in t_lower for w in ["change", "make"]) and any(w in t_lower for w in ["into", " to ", " a ", " an "]) and not any(w in t_lower for w in ["wider", "longer", "bigger", "smaller", "cramped", "spacious", "private", "open"])
        ):
            old_type, new_type, old_id = self._extract_replace_rooms(t_lower, plan)
            if old_type and new_type:
                ops.append(ArchitecturalOperation(
                    type=ArchitecturalActionType.REPLACE_ROOM,
                    target_room=old_type,
                    target_id=old_id,
                    source_room=new_type,
                ))
                return ops, None

        # ---- ROOM REMOVAL -----------------------------------------------
        if any(w in t_lower for w in ["remove", "delete", "get rid of", "eliminate"]):
            ops.append(ArchitecturalOperation(
                type=ArchitecturalActionType.REMOVE_ROOM,
                target_room=target_rtype or "balcony",
                target_id=target_rid
            ))
            return ops, None

        # ---- ROOM SWAP --------------------------------------------------
        if any(w in t_lower for w in ["swap", "switch positions"]):
            types = self._extract_all_room_types(t_lower)
            if len(types) >= 2:
                ops.append(ArchitecturalOperation(
                    type=ArchitecturalActionType.SWAP_ROOMS,
                    target_room=types[0],
                    source_room=types[1]
                ))
                return ops, None

        # ---- MOVEMENT / RELOCATION --------------------------------------
        if any(w in t_lower for w in ["move", "relocate", "shift", "put"]):
            anchor = self._extract_anchor_room(t_lower, exclude_type=target_rtype)
            rel = self.ontology.resolve_spatial_relation(t_lower) or "beside"
            ops.append(ArchitecturalOperation(
                type=ArchitecturalActionType.MOVE_ROOM,
                target_room=target_rtype,
                target_id=target_rid,
                relative_target=anchor,
                spatial_relation=rel
            ))
            return ops, None

        # ---- RESIZING / WIDTH / LENGTH ----------------------------------
        if any(w in t_lower for w in ["wider", "width", "broad"]):
            ops.append(ArchitecturalOperation(
                type=ArchitecturalActionType.CHANGE_WIDTH,
                target_room=target_rtype, target_id=target_rid,
                dimension=DimensionSpec(value=val or 2.0, unit="ft", direction="increase")
            ))
            return ops, None

        if any(w in t_lower for w in ["longer", "length"]):
            ops.append(ArchitecturalOperation(
                type=ArchitecturalActionType.CHANGE_LENGTH,
                target_room=target_rtype, target_id=target_rid,
                dimension=DimensionSpec(value=val or 2.0, unit="ft", direction="increase")
            ))
            return ops, None

        if any(w in t_lower for w in ["bigger", "larger", "enlarge", "expand", "increase"]):
            ops.append(ArchitecturalOperation(
                type=ArchitecturalActionType.RESIZE_ROOM,
                target_room=target_rtype, target_id=target_rid,
                dimension=DimensionSpec(value=val or 2.0, unit="ft", direction="increase")
            ))
            return ops, None

        if any(w in t_lower for w in ["smaller", "reduce", "shrink", "decrease", "compact"]):
            ops.append(ArchitecturalOperation(
                type=ArchitecturalActionType.RESIZE_ROOM,
                target_room=target_rtype, target_id=target_rid,
                dimension=DimensionSpec(value=val or 2.0, unit="ft", direction="decrease")
            ))
            return ops, None

        # Fallback resize if room is known
        if target_rtype:
            ops.append(ArchitecturalOperation(
                type=ArchitecturalActionType.RESIZE_ROOM,
                target_room=target_rtype, target_id=target_rid,
                dimension=DimensionSpec(value=val or 2.0, unit="ft", direction="increase")
            ))
            return ops, None

        return [], "Could you please specify which room you would like to modify?"

    # =======================================================================
    # Helper utilities
    # =======================================================================
    def _push_entity(self, room_id: Optional[str], room_type: Optional[str]):
        if room_type:
            self._entity_stack.append(DiscourseEntity(room_id, room_type, self._turn_index))
            if len(self._entity_stack) > 5:
                self._entity_stack.pop(0)

    def _current_entity_dict(self) -> Dict[str, str]:
        out = {}
        if self._entity_stack:
            top = self._entity_stack[-1]
            out["target_type"] = top.room_type or ""
            out["target_id"] = top.room_id or ""
        return out

    def _extract_source_room(self, text: str, plan: Optional[Any]) -> Tuple[Optional[str], Optional[str]]:
        m = re.search(r'(?:from|take\s+(?:space\s+from|from)?|reduce|use\s+some\s+space\s+from|use\s+some\s+of\s+the)\s+([a-z0-9_\s]+?)(?:for|to|give|and|instead|$)', text)
        if m:
            rtype = self.ontology.resolve_room_type(m.group(1).strip())
            if rtype:
                rid = None
                if plan and hasattr(plan, "rooms"):
                    matching = [r for r in plan.rooms if r.type == rtype]
                    if matching:
                        rid = matching[0].id
                return rtype, rid
        return None, None

    def _extract_destination_room(self, text: str, plan: Optional[Any]) -> Tuple[Optional[str], Optional[str]]:
        m = re.search(r'(?:to|for|give\s+(?:it\s+to|space\s+to)?)\s+([a-z0-9_\s]+?)(?:$|\.|\s+instead)', text)
        if m:
            rtype = self.ontology.resolve_room_type(m.group(1).strip())
            if rtype:
                rid = None
                if plan and hasattr(plan, "rooms"):
                    matching = [r for r in plan.rooms if r.type == rtype]
                    if matching:
                        rid = matching[0].id
                return rtype, rid
        return None, None

    def _extract_anchor_room(self, text: str, exclude_type: Optional[str] = None) -> Optional[str]:
        m = re.search(r'(?:of|to|beside|near|next to|in|at|attached to)\s+(?:the\s+)?([a-z0-9_\s]+)', text)
        if m:
            candidate = self.ontology.resolve_room_type(m.group(1).strip())
            if candidate and candidate != exclude_type:
                return candidate
        if re.search(r'\b(it|this|that)\b', text) and self._entity_stack:
            return self._entity_stack[-1].room_type
        return None

    def _extract_all_room_types(self, text: str) -> List[str]:
        found = []
        for syn, canonical in sorted(SYNONYM_TO_CANONICAL.items(),
                                      key=lambda x: len(x[0]), reverse=True):
            pattern = r'\b' + re.escape(syn) + r'\b'
            if re.search(pattern, text.lower()) and canonical not in found:
                found.append(canonical)
        return found

    def _extract_added_room_type(self, text: str) -> Optional[str]:
        t = text.lower()
        # Direct check before spatial prepositions
        pre_anchor = re.split(r'\b(?:on\s+the\s+right|on\s+the\s+left|on\s+top|on|to|at|in|beside|near|next\s+to|attached\s+to|above|below|for)\b', t)[0].strip()

        inferred = self.ontology.infer_functional_room_type(pre_anchor) or self.ontology.infer_functional_room_type(t)
        if inferred:
            return inferred

        m = re.search(r'(?:add|insert|create|need|want|include|build|put\s*in)\s+(?:\b(?:a|an|one|another|small|large|new|extra)\b\s*)*([a-z0-9_\s]+)', pre_anchor)
        if m:
            candidate = m.group(1).strip()
            rtype = self.ontology.resolve_room_type(candidate)
            if rtype:
                return rtype

        for syn, canonical in sorted(SYNONYM_TO_CANONICAL.items(),
                                      key=lambda x: len(x[0]), reverse=True):
            if syn == "room":
                continue
            if re.search(r'\b' + re.escape(syn) + r'\b', pre_anchor):
                return canonical
        return None

    def _extract_replace_rooms(self, text: str, plan: Optional[Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        t = text.lower()
        old_type = None
        new_type = None
        old_id = None

        # Pattern 1: "replace X with/by/for Y"
        m1 = re.search(r'replace\s+(?:the\s+)?([a-z0-9_\s]+?)\s+(?:with|by|for)\s+(?:a\s+|an\s+|the\s+)?([a-z0-9_\s]+)', t)
        if m1:
            old_str, new_str = m1.group(1).strip(), m1.group(2).strip()
            old_type = self._resolve_single_room_ref(old_str, plan)
            new_type = self.ontology.infer_functional_room_type(new_str) or self.ontology.resolve_room_type(new_str)

        # Pattern 2: "convert/turn/transform/change X into/to Y"
        if not (old_type and new_type):
            m2 = re.search(r'(?:convert|turn|transform|change)\s+(?:the\s+)?([a-z0-9_\s]+?)\s+(?:into|in\s*to|to)\s+(?:a\s+|an\s+|the\s+)?([a-z0-9_\s]+)', t)
            if m2:
                old_str, new_str = m2.group(1).strip(), m2.group(2).strip()
                old_type = self._resolve_single_room_ref(old_str, plan)
                new_type = self.ontology.infer_functional_room_type(new_str) or self.ontology.resolve_room_type(new_str)

        # Pattern 3: "make X a/an/into Y"
        if not (old_type and new_type):
            m3 = re.search(r'make\s+(?:the\s+)?([a-z0-9_\s]+?)\s+(?:into\s+|a\s+|an\s+)([a-z0-9_\s]+)', t)
            if m3:
                old_str, new_str = m3.group(1).strip(), m3.group(2).strip()
                old_type = self._resolve_single_room_ref(old_str, plan)
                new_type = self.ontology.infer_functional_room_type(new_str) or self.ontology.resolve_room_type(new_str)

        # Pronoun fallback for old_type ("replace it with X", "turn it into Y")
        if not old_type and re.search(r'\b(it|this|that|that room|the room)\b', t):
            if self._entity_stack:
                old_type = self._entity_stack[-1].room_type
                old_id = self._entity_stack[-1].room_id

        # Resolve old_id in plan if available
        if old_type and not old_id and plan and hasattr(plan, "rooms"):
            matching = [r for r in plan.rooms if r.type == old_type]
            if matching:
                old_id = matching[0].id

        return old_type, new_type, old_id

    def _resolve_single_room_ref(self, ref_str: str, plan: Optional[Any]) -> Optional[str]:
        ref_str = ref_str.strip()
        if re.search(r'\b(it|this|that|that room|the room)\b', ref_str):
            if self._entity_stack:
                return self._entity_stack[-1].room_type
        if "other bedroom" in ref_str or "second bedroom" in ref_str or "bedroom 2" in ref_str:
            return "bedroom"
        if "master" in ref_str:
            return "master_bedroom"
        return self.ontology.infer_functional_room_type(ref_str) or self.ontology.resolve_room_type(ref_str)
