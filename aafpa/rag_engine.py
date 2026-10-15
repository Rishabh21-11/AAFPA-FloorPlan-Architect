"""
AAFPA 2.0 Semantic Architectural RAG Engine
Provides priority-aware, semantic vector retrieval of National Building Code (NBC 2016),
Model Building Bye-Laws (MBBL 2016), spatial standards, daylighting, ventilation, and Vastu rules.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class ArchitecturalRule:
    rule_id: str
    rule: str
    source: str
    jurisdiction: str
    priority: int                   # 0: User Req, 1: NBC Hard, 2: Validity, 3: Function, 4: Environment, 5: Vastu
    hard_soft: str                  # 'HARD', 'SOFT', 'PREFERENCE'
    applies_to: List[str]
    constraint_type: str
    value: Optional[float] = None
    unit: Optional[str] = None
    verified: bool = True
    explanation_template: str = ""

NBC_AND_ARCHITECTURAL_KNOWLEDGE_BASE = [
    ArchitecturalRule("NBC-HAB-001", "Every habitable room shall have minimum floor area of 9.5 sq.m (~100 sqft) for primary bedrooms and 7.5 sq.m (~80 sqft) for other habitable rooms.",
                     "NBC 2016 Part 3", "national_code", 1, "HARD",
                     ["bedroom", "master_bedroom", "living_room", "study"], "minimum_area", 80.0, "sqft", True,
                     "NBC 2016 mandates habitable rooms must provide at least 80 sqft for human comfort and air volume."),

    ArchitecturalRule("NBC-HAB-002", "Master bedroom minimum floor area shall be >= 120 sqft (11.1 sq.m).",
                     "NBC 2016 Part 3", "national_code", 1, "HARD",
                     ["master_bedroom"], "minimum_area", 120.0, "sqft", True,
                     "Master bedroom must accommodate queen/king bed, circulation, and wardrobe clearance."),

    ArchitecturalRule("NBC-HAB-003", "Every habitable room minimum width shall be >= 2.4m (~7.0 ft).",
                     "NBC 2016 Part 3", "national_code", 1, "HARD",
                     ["bedroom", "master_bedroom", "living_room", "dining", "study"], "minimum_width", 7.0, "ft", True,
                     "NBC 2016 requires minimum width of 2.4m to prevent narrow unusable corridor-shaped rooms."),

    ArchitecturalRule("NBC-BATH-001", "Bathroom minimum floor area shall be >= 1.8 sq.m (~20 sqft).",
                     "NBC 2016 Part 8", "national_code", 1, "HARD",
                     ["bathroom"], "minimum_area", 20.0, "sqft", True,
                     "Sanitary bye-laws require minimum 20 sqft for water closet, washbasin, and shower space."),

    ArchitecturalRule("NBC-BATH-002", "Bathroom minimum width shall be >= 1.2m (~3.5 ft).",
                     "NBC 2016 Part 8", "national_code", 1, "HARD",
                     ["bathroom"], "minimum_width", 3.5, "ft", True,
                     "Minimum 3.5 ft width is required for fixture ergonomics and door swing clearance."),

    ArchitecturalRule("NBC-KITCHEN-001", "Kitchen minimum floor area shall be >= 4.5 sq.m (~48 sqft).",
                     "NBC 2016 Part 3", "national_code", 1, "HARD",
                     ["kitchen"], "minimum_area", 48.0, "sqft", True,
                     "Kitchen requires at least 48 sqft for cooking counter, sink, refrigerator, and circulation."),

    ArchitecturalRule("NBC-VENT-001", "Ventilation and natural lighting aperture opening ratio >= 1/10th of floor area.",
                     "NBC 2016 Part 3", "national_code", 1, "HARD",
                     ["bedroom", "master_bedroom", "living_room", "kitchen", "dining"], "ventilation_ratio", 0.10, "ratio", True,
                     "Exterior window glazing must equal at least 10% of floor area for adequate natural lighting."),

    ArchitecturalRule("NBC-EGRESS-001", "Egress door clear opening width shall be >= 0.9m (~3.0 ft).",
                     "NBC 2016 Part 4", "national_code", 1, "HARD",
                     ["all"], "egress", 3.0, "ft", True,
                     "Fire and life safety code specifies minimum 3ft clear width for primary entrance and exit doors."),

    ArchitecturalRule("MBL-CIRC-001", "Internal corridor minimum clear width shall be >= 0.9m (~3.0 ft).",
                     "Model Building Bye-Laws 2016", "model_bye_law", 1, "HARD",
                     ["corridor"], "minimum_width", 3.0, "ft", True,
                     "Internal corridors must allow unobstructed two-person passing clearance."),

    ArchitecturalRule("VALID-OVERLAP-001", "No two rooms shall overlap in 2D coordinate space.",
                     "Basic Validity", "practice", 2, "HARD",
                     ["all"], "no_overlap", 0.0, "ft", True,
                     "Fundamental geometric consistency: rooms must form a non-overlapping planar partition."),

    ArchitecturalRule("FUNC-ADJ-001", "Kitchen is preferred directly adjacent to dining room.",
                     "Architectural Practice", "practice", 3, "SOFT",
                     ["kitchen", "dining"], "adjacency_preferred", 1.0, "", True,
                     "Adjacent kitchen and dining minimizes food service travel distance."),

    ArchitecturalRule("FUNC-ADJ-002", "Living room is preferred adjacent to entrance/foyer.",
                     "Architectural Practice", "practice", 3, "SOFT",
                     ["living_room", "foyer"], "adjacency_preferred", 1.0, "", True,
                     "Front entry directly into living zone maintains public/private spatial zoning hierarchy."),

    ArchitecturalRule("FUNC-WET-001", "Wet areas (bathrooms, kitchen, utility) should cluster for plumbing efficiency.",
                     "Architectural Practice", "practice", 3, "SOFT",
                     ["kitchen", "bathroom", "utility"], "wet_area_clustering", 1.0, "", True,
                     "Clustered plumbing reduces pipe runs, water hammer, and construction costs."),

    ArchitecturalRule("ENV-LIGHT-001", "Habitable rooms should maintain direct perimeter facade exposure.",
                     "Environmental Design", "practice", 4, "SOFT",
                     ["bedroom", "master_bedroom", "living_room"], "natural_daylight", 1.0, "", True,
                     "Perimeter exterior facade placement ensures natural illumination and visual comfort."),

    ArchitecturalRule("VASTU-ENT-001", "Main entrance preferred in North or East direction.",
                     "Vastu Shastra", "vastu", 5, "PREFERENCE",
                     ["foyer", "entrance"], "vastu_direction", 0.0, "deg", False,
                     "Vastu tradition associates North/East entry with positive solar energy and prosperity."),

    ArchitecturalRule("VASTU-KITCHEN-001", "Kitchen preferred in South-East (Agni corner).",
                     "Vastu Shastra", "vastu", 5, "PREFERENCE",
                     ["kitchen"], "vastu_direction", 135.0, "deg", False,
                     "South-East alignment harnesses prevailing morning winds and fire element alignment."),

    ArchitecturalRule("VASTU-MASTER-001", "Master bedroom preferred in South-West (Nairuthi corner).",
                     "Vastu Shastra", "vastu", 5, "PREFERENCE",
                     ["master_bedroom"], "vastu_direction", 225.0, "deg", False,
                     "South-West placement provides privacy, stability, and protection from harsh afternoon heat.")
]

class SemanticRAGEngine:
    """Semantic vector retriever for architectural knowledge rules."""

    def __init__(self, rules: Optional[List[ArchitecturalRule]] = None):
        self.rules = rules or NBC_AND_ARCHITECTURAL_KNOWLEDGE_BASE
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self._doc_texts = [f"{r.rule} {r.constraint_type} {' '.join(r.applies_to)} {r.source} {r.explanation_template}" for r in self.rules]
        self.doc_vectors = self.vectorizer.fit_transform(self._doc_texts)

    def retrieve(self, query: str, top_k: int = 5,
                 priority_filter: Optional[int] = None) -> List[ArchitecturalRule]:
        """Retrieves top-k most relevant architectural rules matching query."""
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.doc_vectors)[0]

        # Priority weighting: boost hard NBC code rules
        scored_rules = []
        for idx, r in enumerate(self.rules):
            score = float(sims[idx])
            # Boost higher priority rules (lower priority number)
            priority_weight = 1.0 + (5 - r.priority) * 0.1
            final_score = score * priority_weight

            if priority_filter is None or r.priority <= priority_filter:
                scored_rules.append((final_score, r))

        scored_rules.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored_rules[:top_k]]

    def get_applicable_rules(self, room_types: List[str]) -> List[ArchitecturalRule]:
        """Returns all mandatory and functional rules applicable to given room types."""
        applicable = []
        for r in self.rules:
            if "all" in r.applies_to or any(rt in r.applies_to for rt in room_types):
                applicable.append(r)
        return applicable
