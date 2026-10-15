"""
AAFPA 2.0 Universal Architectural Action Language & Schema
Defines structured intermediate representation (IR) for all architectural operations,
constraints, objectives, and multi-step dependency execution graphs.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Dict, Any, List, Union

class ArchitecturalActionType(str, Enum):
    # Room-level modifications
    ADD_ROOM = "ADD_ROOM"
    ADD_CUSTOM_ROOM = "ADD_CUSTOM_ROOM"
    ADD_ROOM_CONDITIONAL = "ADD_ROOM_CONDITIONAL"
    REMOVE_ROOM = "REMOVE_ROOM"
    REPLACE_ROOM = "REPLACE_ROOM"
    RENAME_ROOM = "RENAME_ROOM"
    SWAP_ROOMS = "SWAP_ROOMS"
    MERGE_ROOMS = "MERGE_ROOMS"
    SPLIT_ROOM = "SPLIT_ROOM"
    CONVERT_ROOM = "CONVERT_ROOM"
    
    # Geometric & Dimensional
    RESIZE_ROOM = "RESIZE_ROOM"
    CHANGE_WIDTH = "CHANGE_WIDTH"
    CHANGE_LENGTH = "CHANGE_LENGTH"
    CHANGE_AREA = "CHANGE_AREA"
    TRANSFER_AREA = "TRANSFER_AREA"
    MOVE_ROOM = "MOVE_ROOM"
    ROTATE_ROOM = "ROTATE_ROOM"
    CHANGE_SHAPE = "CHANGE_SHAPE"
    CHANGE_POSITION = "CHANGE_POSITION"
    SET_EXACT_DIMENSION = "SET_EXACT_DIMENSION"
    MODIFY_DIMENSION = "MODIFY_DIMENSION"
    MODIFY_TOPOLOGY = "MODIFY_TOPOLOGY"
    
    # Topological & Adjacency
    ADD_ADJACENCY = "ADD_ADJACENCY"
    REMOVE_ADJACENCY = "REMOVE_ADJACENCY"
    CHANGE_ADJACENCY = "CHANGE_ADJACENCY"
    
    # Apertures (Doors & Windows)
    ADD_DOOR = "ADD_DOOR"
    REMOVE_DOOR = "REMOVE_DOOR"
    MOVE_DOOR = "MOVE_DOOR"
    RESIZE_DOOR = "RESIZE_DOOR"
    RELOCATE_DOOR = "RELOCATE_DOOR"
    RELOCATE_DOOR_FOR_PRIVACY = "RELOCATE_DOOR_FOR_PRIVACY"
    ADD_WINDOW = "ADD_WINDOW"
    REMOVE_WINDOW = "REMOVE_WINDOW"
    MOVE_WINDOW = "MOVE_WINDOW"
    RESIZE_WINDOW = "RESIZE_WINDOW"
    INCREASE_WINDOW_SIZE = "INCREASE_WINDOW_SIZE"
    ADD_WINDOW_CROSS_VENT = "ADD_WINDOW_CROSS_VENT"
    
    # Structural features
    ADD_BALCONY = "ADD_BALCONY"
    REMOVE_BALCONY = "REMOVE_BALCONY"
    ADD_STAIRCASE = "ADD_STAIRCASE"
    REMOVE_STAIRCASE = "REMOVE_STAIRCASE"
    
    # High-level Design Objectives
    IMPROVE_VENTILATION = "IMPROVE_VENTILATION"
    IMPROVE_LIGHTING = "IMPROVE_LIGHTING"
    IMPROVE_PRIVACY = "IMPROVE_PRIVACY"
    IMPROVE_CIRCULATION = "IMPROVE_CIRCULATION"
    MAKE_OPEN_CONCEPT = "MAKE_OPEN_CONCEPT"
    OPTIMIZE_SPACE = "OPTIMIZE_SPACE"
    APPLY_VASTU = "APPLY_VASTU"
    
    # Plan Version & Session Control
    SELECT_LAYOUT = "SELECT_LAYOUT"
    UNDO = "UNDO"
    REDO = "REDO"
    REVERT_STATE = "REVERT_STATE"
    RESTORE_VERSION = "RESTORE_VERSION"
    EXPLAIN_PLAN = "EXPLAIN_PLAN"
    FINALIZE_PLAN = "FINALIZE_PLAN"
    NO_OP_CHAT = "NO_OP_CHAT"
    RAISE_USER_EXCEPTION = "RAISE_USER_EXCEPTION"
    CLARIFICATION_RESPONSE = "CLARIFICATION_RESPONSE"

@dataclass
class DimensionSpec:
    value: Optional[float] = None
    unit: str = "ft"                 # 'ft', 'sqft', 'meters', 'percent'
    direction: Optional[str] = None  # 'increase', 'decrease', 'set_exact'
    qualitative: Optional[str] = None # 'slightly', 'significantly', 'minimum_code'

@dataclass
class ArchitecturalOperation:
    type: ArchitecturalActionType
    target_room: Optional[str] = None         # Canonical type or specific ID (e.g. 'bedroom_2')
    target_id: Optional[str] = None           # Exact room ID in active plan (e.g. 'bed_2')
    source_room: Optional[str] = None         # For transfers/swaps/replaces
    source_id: Optional[str] = None
    dimension: Optional[DimensionSpec] = None
    spatial_relation: Optional[str] = None    # 'above', 'below', 'left', 'right', 'beside', 'corner'
    relative_target: Optional[str] = None     # e.g. "master_bedroom" in "beside master bedroom"
    zone: Optional[str] = None                # 'public', 'private', 'service'
    preserve_adjacent: bool = True
    hard_constraints: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['type'] = self.type.value if isinstance(self.type, ArchitecturalActionType) else self.type
        return d

@dataclass
class StructuredArchitecturalIntent:
    intent_category: str                      # 'modify_layout', 'generate_layout', 'select_layout', 'query_plan', 'undo'
    message_type: str = "architectural_action" # 'conversation', 'question', 'architectural_action', 'undo', 'clarification', 'infeasible'
    operations: List[ArchitecturalOperation] = field(default_factory=list)
    preserve_rooms: List[str] = field(default_factory=list)
    hard_constraints: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=lambda: [
        "preserve_other_rooms",
        "maintain_minimum_room_dimensions",
        "avoid_overlap",
        "maintain_connectivity",
        "respect_plot_boundary"
    ])
    engine_orders: List[Dict[str, Any]] = field(default_factory=list)
    architectural_reasoning: str = ""
    clarification_needed: bool = False
    clarification_question: Optional[str] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    raw_prompt: str = ""
    resolved_references: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_category": self.intent_category,
            "message_type": self.message_type,
            "operations": [op.to_dict() for op in self.operations],
            "preserve_rooms": self.preserve_rooms,
            "hard_constraints": self.hard_constraints,
            "constraints": self.constraints,
            "engine_orders": self.engine_orders,
            "architectural_reasoning": self.architectural_reasoning,
            "clarification_needed": self.clarification_needed,
            "clarification_question": self.clarification_question,
            "user_preferences": self.user_preferences,
            "raw_prompt": self.raw_prompt,
            "resolved_references": self.resolved_references
        }
