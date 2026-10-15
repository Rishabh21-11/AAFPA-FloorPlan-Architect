"""
AAFPA 2.0 - AI Agentic Floor Plan Architect
Universal package exports for ontology, structured actions, smart agent,
architect engine tools, spatial reasoning, parametric geometry modification,
dataset pipeline, RAG, and interactive studio.
"""

from aafpa.ontology import ArchitecturalOntology, CANONICAL_ROOM_TYPES, SPATIAL_RELATIONS
from aafpa.actions import (
    ArchitecturalActionType, ArchitecturalOperation, DimensionSpec,
    StructuredArchitecturalIntent
)
from aafpa.spatial_reasoning import SpatialReasoningEngine
from aafpa.semantic_agent import SemanticIntentAgent, PlanMemory
from aafpa.smart_agent import ConditionGroundedSmartAgent, PlanConditionReport, DiscourseEntity
from aafpa.architect_engine_tools import ArchitectEngineFacade, ToolResult
from aafpa.geometry_engine import GenericGeometryEngine
from aafpa.dataset_pipeline import (
    UnifiedFloorPlanDataset,
    HouseMindDatasetLoader,
    HOUSEMIND_ROOM_TYPES,
    RPLAN_ROOM_TYPES,
    CUBICASA_ROOM_TYPES,
)
from aafpa.rag_engine import SemanticRAGEngine, ArchitecturalRule, NBC_AND_ARCHITECTURAL_KNOWLEDGE_BASE
from aafpa.instruction_data import ArchitecturalInstructionDataset
from aafpa.evaluation import EvaluationBenchmark
from aafpa.studio import (
    InteractiveFloorPlanStudioSession, get_studio_session,
    aafpa_chat, aafpa_select_layout, aafpa_finalize, aafpa_edit,
    plan_to_png_bytes, plan_to_dict
)

__version__ = "2.0.1"
__all__ = [
    # Ontology & schema
    "ArchitecturalOntology",
    "CANONICAL_ROOM_TYPES",
    "SPATIAL_RELATIONS",
    # Action IR
    "ArchitecturalActionType",
    "ArchitecturalOperation",
    "DimensionSpec",
    "StructuredArchitecturalIntent",
    # Spatial reasoning
    "SpatialReasoningEngine",
    # Legacy semantic agent (backward-compat)
    "SemanticIntentAgent",
    "PlanMemory",
    # Smart Agent (new)
    "ConditionGroundedSmartAgent",
    "PlanConditionReport",
    "DiscourseEntity",
    # Architect Engine Tool Facade (new)
    "ArchitectEngineFacade",
    "ToolResult",
    # Geometry engine
    "GenericGeometryEngine",
    # Dataset pipeline
    "UnifiedFloorPlanDataset",
    "HouseMindDatasetLoader",
    "HOUSEMIND_ROOM_TYPES",
    "RPLAN_ROOM_TYPES",
    "CUBICASA_ROOM_TYPES",
    # RAG
    "SemanticRAGEngine",
    "ArchitecturalRule",
    "NBC_AND_ARCHITECTURAL_KNOWLEDGE_BASE",
    # Training
    "ArchitecturalInstructionDataset",
    # Evaluation
    "EvaluationBenchmark",
    # Studio
    "InteractiveFloorPlanStudioSession",
    "get_studio_session",
    "aafpa_chat",
    "aafpa_select_layout",
    "aafpa_finalize",
    "aafpa_edit",
]
