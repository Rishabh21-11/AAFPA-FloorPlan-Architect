"""
AAFPA 2.0 Semantic Intent Agent & Conversational Memory Manager
Translates flexible natural language into structured architectural intents,
resolves multi-turn references and relative spatial phrases, and manages plan version history.
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from aafpa.ontology import ArchitecturalOntology, SYNONYM_TO_CANONICAL
from aafpa.actions import (
    ArchitecturalActionType, ArchitecturalOperation, DimensionSpec,
    StructuredArchitecturalIntent
)
from aafpa.spatial_reasoning import SpatialReasoningEngine

class PlanMemory:
    """Manages active plan state, version snapshots, undo/redo, and conversational focus."""
    def __init__(self):
        self.current_plan: Optional[Any] = None
        self.current_req: Optional[Any] = None
        self.current_adj_graph: Optional[Any] = None
        self.history: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self.active_candidates: List[Dict[str, Any]] = []
        self.selected_layout_idx: Optional[int] = None
        self.focused_room_id: Optional[str] = None
        self.focused_room_type: Optional[str] = None
        self.last_operation_type: Optional[str] = None
        self.user_preferences: Dict[str, Any] = {}

    def snapshot(self, description: str = ""):
        """Saves current state into version history."""
        if self.current_plan:
            # Shallow/deep copy of plan state
            import copy
            self.history.append({
                "plan": copy.deepcopy(self.current_plan),
                "req": copy.deepcopy(self.current_req),
                "description": description,
                "version": getattr(self.current_plan, "version", len(self.history) + 1),
                "focused_room_id": self.focused_room_id,
                "focused_room_type": self.focused_room_type
            })
            self.redo_stack.clear()

    def undo(self) -> Optional[Any]:
        """Restores previous plan version."""
        if len(self.history) > 1:
            curr = self.history.pop()
            self.redo_stack.append(curr)
            prev = self.history[-1]
            self.current_plan = prev["plan"]
            self.current_req = prev["req"]
            self.focused_room_id = prev.get("focused_room_id")
            self.focused_room_type = prev.get("focused_room_type")
            return self.current_plan
        return None

    def redo(self) -> Optional[Any]:
        """Redoes previously undone plan version."""
        if self.redo_stack:
            item = self.redo_stack.pop()
            self.history.append(item)
            self.current_plan = item["plan"]
            self.current_req = item["req"]
            self.focused_room_id = item.get("focused_room_id")
            self.focused_room_type = item.get("focused_room_type")
            return self.current_plan
        return None

    def set_focus(self, room_id: Optional[str], room_type: Optional[str]):
        """Updates the conversational focus target for pronoun resolution."""
        if self.focused_room_type and self.focused_room_type != room_type:
            self.previous_focused_room_type = self.focused_room_type
            self.previous_focused_room_id = self.focused_room_id
        if room_id:
            self.focused_room_id = room_id
        if room_type:
            self.focused_room_type = room_type

class SemanticIntentAgent:
    """Interprets natural language into structured architectural intents using semantic analysis."""

    def __init__(self, memory: Optional[PlanMemory] = None):
        self.memory = memory or PlanMemory()
        self.ontology = ArchitecturalOntology()

    def parse_intent(self, text: str, current_plan: Optional[Any] = None) -> StructuredArchitecturalIntent:
        """Parses natural language input into a StructuredArchitecturalIntent."""
        t = text.strip()
        t_lower = t.lower()
        plan = current_plan or (self.memory.current_plan if self.memory else None)

        # 1. Check Meta / Session commands
        # Layout selection (e.g. "select layout 2", "layout 3", "choose 1", "option 4", "2")
        m_sel = re.search(r'\b(?:select|choose|pick|activate|layout|option)\s*#?\s*([1-4])\b', t_lower)
        if not m_sel and re.match(r'^[1-4]$', t_lower.strip()):
            m_sel = re.match(r'^([1-4])$', t_lower.strip())
        if m_sel:
            opt_num = int(m_sel.group(1))
            return StructuredArchitecturalIntent(
                intent_category="select_layout",
                operations=[ArchitecturalOperation(
                    type=ArchitecturalActionType.SELECT_LAYOUT,
                    parameters={"option_number": opt_num}
                )],
                raw_prompt=t
            )

        # Undo / Redo
        if any(w in t_lower for w in ["undo", "revert", "go back", "previous version", "step back"]):
            return StructuredArchitecturalIntent(
                intent_category="undo",
                operations=[ArchitecturalOperation(type=ArchitecturalActionType.UNDO)],
                raw_prompt=t
            )
        if any(w in t_lower for w in ["redo", "step forward"]):
            return StructuredArchitecturalIntent(
                intent_category="redo",
                operations=[ArchitecturalOperation(type=ArchitecturalActionType.REDO)],
                raw_prompt=t
            )
        if any(w in t_lower for w in ["finalize", "lock plan", "done editing", "approve plan"]):
            return StructuredArchitecturalIntent(
                intent_category="finalize_plan",
                operations=[ArchitecturalOperation(type=ArchitecturalActionType.FINALIZE_PLAN)],
                raw_prompt=t
            )

        # 2. Check High-Level Architectural Objectives
        if "ventilat" in t_lower or "airflow" in t_lower or "breeze" in t_lower:
            return StructuredArchitecturalIntent(
                intent_category="modify_layout",
                operations=[ArchitecturalOperation(type=ArchitecturalActionType.IMPROVE_VENTILATION)],
                raw_prompt=t
            )
        if "lighting" in t_lower or "daylight" in t_lower or "sunlight" in t_lower or "bright" in t_lower:
            return StructuredArchitecturalIntent(
                intent_category="modify_layout",
                operations=[ArchitecturalOperation(type=ArchitecturalActionType.IMPROVE_LIGHTING)],
                raw_prompt=t
            )
        if "privacy" in t_lower or "private" in t_lower or "seclude" in t_lower:
            return StructuredArchitecturalIntent(
                intent_category="modify_layout",
                operations=[ArchitecturalOperation(type=ArchitecturalActionType.IMPROVE_PRIVACY)],
                raw_prompt=t
            )
        if "open concept" in t_lower or "open plan" in t_lower or "spacious" in t_lower or "open feel" in t_lower:
            return StructuredArchitecturalIntent(
                intent_category="modify_layout",
                operations=[ArchitecturalOperation(type=ArchitecturalActionType.MAKE_OPEN_CONCEPT)],
                raw_prompt=t
            )
        if "vastu" in t_lower:
            return StructuredArchitecturalIntent(
                intent_category="modify_layout",
                operations=[ArchitecturalOperation(type=ArchitecturalActionType.APPLY_VASTU)],
                raw_prompt=t
            )

        # 3. Multi-Step Request Splitting (e.g. "and", ";", "also", "then")
        # Do not split on 'and' if sentence contains 'swap', 'between', 'replace', or 'transfer'
        if any(w in t_lower for w in ["swap", "replace", "between", "convert", "interchange"]):
            sub_phrases = re.split(r';|\bthen\b', t_lower)
        else:
            sub_phrases = re.split(r'\band\b|\balso\b|\bthen\b|;|,', t_lower)

        operations = []
        resolved_refs = {}

        for sub in sub_phrases:
            sub = sub.strip()
            if not sub or len(sub) < 3:
                continue
            op = self._parse_single_clause(sub, plan, resolved_refs)
            if op:
                operations.append(op)

        if not operations:
            op = self._parse_single_clause(t_lower, plan, resolved_refs)
            if op:
                operations.append(op)

        if not operations:
            return StructuredArchitecturalIntent(
                intent_category="modify_layout",
                clarification_needed=False,
                raw_prompt=t
            )

        return StructuredArchitecturalIntent(
            intent_category="modify_layout",
            operations=operations,
            raw_prompt=t,
            resolved_references=resolved_refs
        )

    def _parse_single_clause(self, text: str, plan: Optional[Any],
                             resolved_refs: Dict[str, str]) -> Optional[ArchitecturalOperation]:
        """Parses a single atomic modification clause."""
        t = text.lower().strip()

        # Resolve pronoun references ("it", "the room", "this room", "them")
        target_rtype, target_rid = self._resolve_target_room(t, plan)
        if target_rid:
            resolved_refs["target_id"] = target_rid
        if target_rtype:
            resolved_refs["target_type"] = target_rtype

        val, unit, scale = self.ontology.parse_dimension_amount(t)

        # A. AREA TRANSFER (e.g. "take 30 sqft from dining for bedroom 2", "reduce bath and give space to bed")
        if ("from" in t and ("to" in t or "for" in t)) or \
           ("take" in t and "from" in t) or \
           ("steal" in t and "from" in t) or \
           ("transfer" in t and "from" in t):
            source_rtype, source_rid = self._extract_source_room(t, plan)
            dest_rtype, dest_rid = self._extract_destination_room(t, plan)
            if not dest_rtype and target_rtype:
                dest_rtype, dest_rid = target_rtype, target_rid

            return ArchitecturalOperation(
                type=ArchitecturalActionType.TRANSFER_AREA,
                target_room=dest_rtype,
                target_id=dest_rid,
                source_room=source_rtype,
                source_id=source_rid,
                dimension=DimensionSpec(value=val or 20.0, unit=unit or "sqft", qualitative=scale)
            )

        # B. SWAP / REPLACE / CONVERT (e.g. "replace study with bedroom", "turn guest room into office", "swap kitchen and dining")
        m_repl = re.search(r'(?:replace|convert|turn)\s+(?:the\s+)?([a-z0-9_\s]+?)\s+(?:with|into|to)\s+(?:a\s+|an\s+)?([a-z0-9_\s]+)', t)
        if m_repl:
            old_r = self.ontology.resolve_room_type(m_repl.group(1).strip())
            new_r = self.ontology.resolve_room_type(m_repl.group(2).strip())
            if old_r and new_r:
                return ArchitecturalOperation(
                    type=ArchitecturalActionType.REPLACE_ROOM,
                    target_room=old_r,
                    source_room=new_r
                )

        if any(w in t for w in ["swap", "interchange", "switch"]):
            r_types = self._extract_all_room_types(t)
            if len(r_types) >= 2:
                return ArchitecturalOperation(
                    type=ArchitecturalActionType.SWAP_ROOMS,
                    target_room=r_types[0],
                    source_room=r_types[1]
                )

        # C. REMOVE / DELETE
        if any(w in t for w in ["remove", "delete", "drop", "get rid of", "don't need", "dont need", "eliminate"]):
            return ArchitecturalOperation(
                type=ArchitecturalActionType.REMOVE_ROOM,
                target_room=target_rtype,
                target_id=target_rid
            )

        # D. ADD / INSERT / CREATE
        if any(w in t for w in ["add", "insert", "create", "i need one more", "include", "put a new", "want a new", "want a small", "want a large"]):
            add_type = self._extract_added_room_type(t) or target_rtype or "foyer"
            spatial_rel = self.ontology.resolve_spatial_relation(t)
            rel_target_type = None

            # Extract anchor room (after "of", "to", "beside", "near", "next to", "in", "starting of")
            m_anchor = re.search(r'(?:of|to|beside|near|next to|in|at|starting of)\s+(?:the\s+)?(?:starting of\s+(?:the\s+)?)?([a-z0-9_\s]+)', t)
            if m_anchor:
                anchor_candidate = self.ontology.resolve_room_type(m_anchor.group(1).strip())
                if anchor_candidate and anchor_candidate != add_type:
                    rel_target_type = anchor_candidate

            if not rel_target_type and bool(re.search(r'\b(it|this|that)\b', t)) and self.memory:
                rel_target_type = self.memory.previous_focused_room_type or self.memory.focused_room_type

            return ArchitecturalOperation(
                type=ArchitecturalActionType.ADD_ROOM,
                target_room=add_type,
                spatial_relation=spatial_rel,
                relative_target=rel_target_type,
                dimension=DimensionSpec(value=val, unit=unit or "sqft", qualitative=scale)
            )

        # E. MOVE / SHIFT / RELOCATE / POSITIONING
        if any(w in t for w in ["move", "shift", "relocate", "put", "place", "push", "bring"]):
            spatial_rel = self.ontology.resolve_spatial_relation(t)
            rel_target_type = None
            if bool(re.search(r'\b(it|this|that)\b', t)) and self.memory:
                rel_target_type = self.memory.previous_focused_room_type or self.memory.focused_room_type
            elif any(w in t for w in ["beside", "next to", "near", "above", "below", "opposite"]):
                for syn, canonical in SYNONYM_TO_CANONICAL.items():
                    if syn in t and canonical != target_rtype:
                        rel_target_type = canonical
                        break

            return ArchitecturalOperation(
                type=ArchitecturalActionType.MOVE_ROOM,
                target_room=target_rtype,
                target_id=target_rid,
                spatial_relation=spatial_rel,
                relative_target=rel_target_type
            )

        # F. RESIZING / DIMENSIONAL CHANGES
        # Contrast phrases like "longer instead of wider" or "longer but not wider"
        if "longer instead of wider" in t or "longer but not wider" in t or "longer rather than wider" in t:
            return ArchitecturalOperation(
                type=ArchitecturalActionType.CHANGE_LENGTH,
                target_room=target_rtype,
                target_id=target_rid,
                dimension=DimensionSpec(value=val or 2.0, unit=unit or "ft", direction="increase", qualitative=scale)
            )
        if "wider instead of longer" in t or "wider but not longer" in t or "wider rather than longer" in t:
            return ArchitecturalOperation(
                type=ArchitecturalActionType.CHANGE_WIDTH,
                target_room=target_rtype,
                target_id=target_rid,
                dimension=DimensionSpec(value=val or 2.0, unit=unit or "ft", direction="increase", qualitative=scale)
            )

        # Length / Depth change
        if any(w in t for w in ["longer", "length", "depth", "deeper", "expand length", "shorter", "decrease length"]):
            is_increase = not any(w in t for w in ["shorter", "reduce length", "decrease length", "shrink length", "less deep"])
            return ArchitecturalOperation(
                type=ArchitecturalActionType.CHANGE_LENGTH,
                target_room=target_rtype,
                target_id=target_rid,
                dimension=DimensionSpec(
                    value=val or 2.0,
                    unit=unit or "ft",
                    direction="increase" if is_increase else "decrease",
                    qualitative=scale
                )
            )

        # Width change
        if any(w in t for w in ["wider", "width", "broad", "broader", "expand width", "narrower", "decrease width"]):
            is_increase = not any(w in t for w in ["narrower", "reduce width", "decrease width", "shrink width", "less wide"])
            return ArchitecturalOperation(
                type=ArchitecturalActionType.CHANGE_WIDTH,
                target_room=target_rtype,
                target_id=target_rid,
                dimension=DimensionSpec(
                    value=val or 2.0,
                    unit=unit or "ft",
                    direction="increase" if is_increase else "decrease",
                    qualitative=scale
                )
            )

        # Area / General size change (give another 20 sqft, bigger, smaller, enlarge, expand, reduce, shrink)
        if any(w in t for w in ["give", "another", "sqft", "square feet", "bigger", "larger", "enlarge", "expand", "increase", "more space", "spacious"]):
            return ArchitecturalOperation(
                type=ArchitecturalActionType.RESIZE_ROOM,
                target_room=target_rtype,
                target_id=target_rid,
                dimension=DimensionSpec(
                    value=val or 2.0,
                    unit=unit or ("sqft" if "sq" in t else "ft"),
                    direction="increase",
                    qualitative=scale
                )
            )
        if any(w in t for w in ["smaller", "reduce", "shrink", "decrease", "less space", "compact"]):
            return ArchitecturalOperation(
                type=ArchitecturalActionType.RESIZE_ROOM,
                target_room=target_rtype,
                target_id=target_rid,
                dimension=DimensionSpec(
                    value=val or 2.0,
                    unit=unit or "ft",
                    direction="decrease",
                    qualitative=scale
                )
            )

        # G. Aperture modifications (doors / windows)
        if "door" in t:
            action = ArchitecturalActionType.ADD_DOOR if "add" in t else (
                     ArchitecturalActionType.REMOVE_DOOR if "remove" in t or "delete" in t else ArchitecturalActionType.MOVE_DOOR)
            return ArchitecturalOperation(type=action, target_room=target_rtype, target_id=target_rid)
        if "window" in t:
            action = ArchitecturalActionType.ADD_WINDOW if "add" in t else (
                     ArchitecturalActionType.REMOVE_WINDOW if "remove" in t or "delete" in t else ArchitecturalActionType.MOVE_WINDOW)
            return ArchitecturalOperation(type=action, target_room=target_rtype, target_id=target_rid)

        # If a target room is identified, default to smart resize
        if target_rtype:
            return ArchitecturalOperation(
                type=ArchitecturalActionType.RESIZE_ROOM,
                target_room=target_rtype,
                target_id=target_rid,
                dimension=DimensionSpec(value=val or 2.0, unit=unit or "ft", direction="increase")
            )

        return None

    def _resolve_target_room(self, text: str, plan: Optional[Any]) -> Tuple[Optional[str], Optional[str]]:
        """Resolves target room type and specific instance ID using plan coordinates and memory."""
        t = text.lower()

        # 1. First check if an explicit room type is mentioned in the text
        rtype = self.ontology.resolve_room_type(t)
        if rtype:
            rid = None
            if plan and hasattr(plan, 'rooms'):
                matching = [r for r in plan.rooms if r.type == rtype or rtype in r.type]
                if matching:
                    rid = matching[0].id
            if self.memory:
                self.memory.set_focus(rid, rtype)
            return rtype, rid

        # 2. Check numbered room instances (e.g. "bedroom 2", "bed 2", "second bedroom", "bathroom 1")
        m_num = re.search(r'(?:bedroom|bed|br)\s*#?\s*([1-3])\b', t) or re.search(r'\b(first|second|third|1st|2nd|3rd)\s*(?:bedroom|bed)\b', t)
        if m_num and plan and hasattr(plan, 'rooms'):
            num_str = m_num.group(1)
            num_idx = 1 if num_str in ("1", "first", "1st") else (2 if num_str in ("2", "second", "2nd") else 3)
            bed_rooms = [r for r in plan.rooms if "bedroom" in r.type or "bed" in r.type]
            if len(bed_rooms) >= num_idx:
                target_r = bed_rooms[num_idx - 1]
                if self.memory:
                    self.memory.set_focus(target_r.id, target_r.type)
                return target_r.type, target_r.id

        # 3. Check relative spatial references (e.g. "the room above it", "the bedroom above the bathroom")
        spatial_rel = self.ontology.resolve_spatial_relation(t)
        if spatial_rel and plan and hasattr(plan, 'rooms'):
            anchor_room = None
            if self.memory and self.memory.focused_room_id:
                anchor_room = next((r for r in plan.rooms if r.id == self.memory.focused_room_id), None)
            matched = SpatialReasoningEngine.find_room_by_spatial_relation(plan.rooms, spatial_rel, anchor_room)
            if matched:
                if self.memory:
                    self.memory.set_focus(matched.id, matched.type)
                return matched.type, matched.id

        # 4. Check pronoun / anaphora ("it", "this", "that room", "the room") when no explicit room was named
        is_pronoun = bool(re.search(r'\b(it|this|that|the room|same room)\b', t))
        if is_pronoun and self.memory and self.memory.focused_room_type:
            return self.memory.focused_room_type, self.memory.focused_room_id

        return None, None

    def _extract_source_room(self, text: str, plan: Optional[Any]) -> Tuple[Optional[str], Optional[str]]:
        """Extracts source room for transfers (e.g. 'take from dining room')."""
        t = text.lower()
        m = re.search(r'(?:from|take\s+(?:space\s+from|from)?|reduce)\s+([a-z0-9_\s]+?)(?:for|to|give|and|$)', t)
        if m:
            src_str = m.group(1).strip()
            rtype = self.ontology.resolve_room_type(src_str)
            if rtype:
                rid = None
                if plan and hasattr(plan, 'rooms'):
                    matching = [r for r in plan.rooms if r.type == rtype]
                    if matching:
                        rid = matching[0].id
                return rtype, rid
        return None, None

    def _extract_destination_room(self, text: str, plan: Optional[Any]) -> Tuple[Optional[str], Optional[str]]:
        """Extracts destination room for transfers (e.g. 'give it to bedroom 2')."""
        t = text.lower()
        m = re.search(r'(?:to|for|give\s+(?:it\s+to|space\s+to)?)\s+([a-z0-9_\s]+?)(?:$|\.)', t)
        if m:
            dest_str = m.group(1).strip()
            rtype = self.ontology.resolve_room_type(dest_str)
            if rtype:
                rid = None
                if plan and hasattr(plan, 'rooms'):
                    matching = [r for r in plan.rooms if r.type == rtype]
                    if matching:
                        rid = matching[0].id
                return rtype, rid
        return None, None

    def _extract_all_room_types(self, text: str) -> List[str]:
        """Extracts all distinct room types mentioned in text."""
        found = []
        for syn, canonical in SYNONYM_TO_CANONICAL.items():
            pattern = r'\b' + re.escape(syn) + r'\b'
            if re.search(pattern, text.lower()) and canonical not in found:
                found.append(canonical)
        return found

    def _extract_added_room_type(self, text: str) -> Optional[str]:
        """Extracts the room type being added."""
        t = text.lower()
        m = re.search(r'(?:add|insert|create|need|want)\s+(?:a|an|one|another|small|large)?\s*([a-z0-9_\s]+?)(?:\s+(?:on|to|at|in|beside|near|attached|adjacent|above|below|next|for|starting)|$)', t)
        if m:
            rtype = self.ontology.resolve_room_type(m.group(1).strip())
            if rtype:
                return rtype

        # Direct search over known synonyms
        for syn, canonical in sorted(SYNONYM_TO_CANONICAL.items(), key=lambda x: len(x[0]), reverse=True):
            if syn in t:
                return canonical
        return None
