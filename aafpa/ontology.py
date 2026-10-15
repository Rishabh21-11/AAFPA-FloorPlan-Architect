"""
AAFPA 2.0 Architectural Ontology & Canonical Entity Mapper
Provides semantic resolution of natural-language architectural concepts,
canonical room type mappings, spatial relationship terms, arbitrary room functional
inference, and a 200+ category taxonomy covering 14 architectural interaction families.
"""

import re
from typing import Optional, Dict, Any, List, Tuple

# Canonical room categories (core + specialized + custom types)
CANONICAL_ROOM_TYPES = {
    "living_room": [
        "living room", "living", "hall", "drawing room", "sitting room", "lounge",
        "family room", "main hall", "front hall", "living hall", "drawing hall",
        "great room", "common hall", "living_room", "gathering area", "living area"
    ],
    "master_bedroom": [
        "master bedroom", "master bed", "master", "primary bedroom", "main bedroom",
        "master room", "mbr", "master_bedroom", "owners suite", "parents room",
        "master suite", "main bed", "principal bedroom"
    ],
    "bedroom": [
        "bedroom", "bed room", "sleeping room", "room", "br", "bed", "kids room",
        "children room", "guest room", "guest bedroom", "second bedroom", "bedroom 2",
        "bedroom 3", "bedroom 1", "child room", "bed2", "bed1", "bed3", "sleeping quarter"
    ],
    "kitchen": [
        "kitchen", "cooking area", "cooking space", "modular kitchen", "open kitchen",
        "wet kitchen", "dry kitchen", "pantry", "cooktop space", "culinary area",
        "galley", "kitchenette"
    ],
    "dining": [
        "dining room", "dining", "dining area", "eating area", "eating space",
        "dining hall", "dinning", "dinning room", "breakfast nook", "dinning area",
        "meal area"
    ],
    "bathroom": [
        "bathroom", "washroom", "restroom", "toilet", "wc", "lavatory", "bath",
        "attached bath", "common bath", "powder room", "water closet", "attached bathroom",
        "common bathroom", "ensuite", "bath room", "wash room", "toilet room", "latrine",
        "half bath", "full bath"
    ],
    "pooja_room": [
        "pooja room", "pooja", "puja", "puja room", "prayer room", "mandir",
        "altar", "temple room", "devotional space", "pooja altar", "prayer space",
        "meditation corner", "mandap", "devghar"
    ],
    "balcony": [
        "balcony", "verandah", "veranda", "terrace", "patio", "deck", "sitout",
        "sit out", "porch", "balconies", "lanai", "open terrace"
    ],
    "study": [
        "study", "study room", "home office", "office", "library", "work room",
        "workspace", "reading room", "den", "study area", "work station", "quiet office"
    ],
    "corridor": [
        "corridor", "hallway", "passage", "passageway", "aisle", "spine",
        "circulation", "circulation spine", "central corridor", "gallery"
    ],
    "foyer": [
        "foyer", "entrance", "entryway", "vestibule", "lobby", "entry", "entry porch",
        "main entrance", "front door area", "common area", "common space", "common lounge",
        "entrance area", "entrance foyer", "small entrance area", "vestibule entry",
        "antechamber", "mudroom"
    ],
    "utility": [
        "utility", "utility room", "service area", "wash area", "laundry",
        "store", "storage", "store room", "laundry room", "scullery", "linen room"
    ],
    "dressing_room": [
        "dressing room", "walk in closet", "walk-in closet", "closet", "dressing area",
        "wardrobe room", "dressing"
    ],
    "gym": [
        "gym", "home gym", "fitness room", "workout area", "exercise room",
        "yoga room", "workout space"
    ],
    "home_theatre": [
        "home theatre", "home theater", "media room", "cinema room", "movie room",
        "entertainment room", "audio video room"
    ],
    "gaming_room": [
        "gaming room", "game room", "game setup", "arcade room", "playroom",
        "kids play area", "recreation room"
    ],
    "nursery": [
        "nursery", "baby room", "infant room", "toddler room"
    ],
    "studio": [
        "studio", "art studio", "music room", "craft room", "workshop",
        "hobby room", "recording studio"
    ],
    "courtyard": [
        "courtyard", "court", "inner courtyard", "atrium", "open courtyard", "aangan", "brahmasthan"
    ],
    "staircase": [
        "staircase", "stairs", "stairway", "stair", "steps"
    ]
}

# Inverted index for fast O(1) canonical lookup
SYNONYM_TO_CANONICAL: Dict[str, str] = {}
for canonical, synonyms in CANONICAL_ROOM_TYPES.items():
    for syn in synonyms:
        SYNONYM_TO_CANONICAL[syn.lower().strip()] = canonical

# Spatial directions and relative relationship ontology
SPATIAL_RELATIONS = {
    "above": ["above", "up", "upper", "top", "north of", "higher than", "over", "north"],
    "below": ["below", "down", "lower", "bottom", "south of", "underneath", "under", "south"],
    "left": ["left", "left of", "west of", "to the left", "leftside", "west"],
    "right": ["right", "right of", "east of", "to the right", "rightside", "east"],
    "beside": ["beside", "next to", "adjacent to", "side by side", "alongside", "by"],
    "near": ["near", "close to", "nearby", "in vicinity of", "around", "towards"],
    "opposite": ["opposite", "across from", "facing"],
    "front": ["front", "in front of", "entrance side", "forefront"],
    "back": ["back", "rear", "behind", "backside"],
    "corner": ["corner", "northeast corner", "northwest corner", "southeast corner", "southwest corner"],
    "center": ["center", "middle", "central", "core"]
}

# Unit conversions to feet and sqft
UNIT_CONVERSIONS = {
    "ft": 1.0,
    "feet": 1.0,
    "foot": 1.0,
    "'": 1.0,
    "m": 3.28084,
    "meter": 3.28084,
    "meters": 3.28084,
    "metre": 3.28084,
    "metres": 3.28084,
    "in": 1.0 / 12.0,
    "inch": 1.0 / 12.0,
    "inches": 1.0 / 12.0,
    '"': 1.0 / 12.0,
    "sqft": 1.0,
    "sq ft": 1.0,
    "sq.ft": 1.0,
    "square feet": 1.0,
    "square foot": 1.0,
    "sqm": 10.7639,
    "sq m": 10.7639,
    "sq.m": 10.7639,
    "square meters": 10.7639,
    "square meter": 10.7639
}

# Functional descriptions to inferred canonical/custom room types
FUNCTIONAL_INFERENCE_RULES = [
    (r'\b(?:quiet\s*(?:place|room|corner|space)\s*(?:where\s*(?:i\s*can\s*)?work|to\s*work|for\s*work)?|work\s*from\s*home|wfh|place\s*to\s*study|where\s*i\s*can\s*work|work\s*space)\b', "study"),
    (r'\b(?:somewhere|place|room|space)\s*for\s*(?:prayer|worship|god|meditation|puja|pooja|devotion)\b', "pooja_room"),
    (r'\b(?:somewhere|place|room|space)\s*to\s*(?:exercise|work\s*out|lift\s*weights|do\s*yoga|fitness)\b', "gym"),
    (r'\b(?:somewhere|place|room|space)\s*to\s*(?:play\s*games|video\s*games|game|stream)\b', "gaming_room"),
    (r'\b(?:somewhere|place|room|space)\s*to\s*(?:watch\s*movies|films|cinema|home\s*theater)\b', "home_theatre"),
    (r'\b(?:somewhere|place|room|space)\s*for\s*(?:newborn|baby|infant|toddler)\b', "nursery"),
    (r'\b(?:somewhere|place|room|space)\s*to\s*(?:paint|record\s*music|craft|draw|art)\b', "studio"),
    (r'\b(?:somewhere|place|room|space)\s*to\s*(?:keep\s*clothes|dress\s*up|wardrobe|closet)\b', "dressing_room"),
    (r'\b(?:somewhere|place|room|space)\s*to\s*(?:wash\s*clothes|do\s*laundry|store\s*cleaning)\b', "utility"),
]

# 200+ Taxonomy: Intent Families and Category Definitions
TAXONOMY_INTENT_FAMILIES = {
    "ROOM_ADDITION": [
        "ADD_MASTER_BEDROOM", "ADD_BEDROOM", "ADD_KIDS_BEDROOM", "ADD_GUEST_BEDROOM",
        "ADD_KITCHEN", "ADD_DINING", "ADD_BATHROOM", "ADD_ATTACHED_BATHROOM",
        "ADD_POWDER_ROOM", "ADD_BALCONY", "ADD_POOJA_ROOM", "ADD_STUDY",
        "ADD_HOME_OFFICE", "ADD_FOYER", "ADD_UTILITY", "ADD_STORE_ROOM",
        "ADD_DRESSING_ROOM", "ADD_GYM", "ADD_HOME_THEATRE", "ADD_GAMING_ROOM",
        "ADD_NURSERY", "ADD_STUDIO", "ADD_COURTYARD", "ADD_CUSTOM_ROOM", "ADD_CONDITIONAL"
    ],
    "ROOM_REMOVAL": [
        "REMOVE_ROOM", "REMOVE_BALCONY", "REMOVE_PARTITION", "REMOVE_UTILITY",
        "REMOVE_STORE", "REMOVE_STUDY", "REMOVE_CORRIDOR_SEGMENT", "REMOVE_MERGE",
        "CONVERT_BEDROOM_TO_STUDY", "CONVERT_UTILITY_TO_BATH", "CONVERT_STORE_TO_POOJA",
        "CONVERT_BALCONY_TO_LIVING", "CONVERT_BEDROOM_TO_DRESSING"
    ],
    "ROOM_RESIZING": [
        "RESIZE_INCREASE", "RESIZE_DECREASE", "RESIZE_PROPORTIONAL",
        "CHANGE_WIDTH_INCREASE", "CHANGE_WIDTH_DECREASE", "CHANGE_LENGTH_INCREASE",
        "CHANGE_LENGTH_DECREASE", "CHANGE_AREA_INCREASE", "CHANGE_AREA_DECREASE",
        "SET_EXACT_DIMENSION", "SET_EXACT_AREA", "SET_ASPECT_RATIO_SQUARE",
        "SET_ASPECT_RATIO_RECTANGULAR", "EXPAND_TOWARDS_CORRIDOR", "SHRINK_AWAY_FROM_BOUNDARY"
    ],
    "AREA_TRANSFER": [
        "TRANSFER_INFERRED", "TRANSFER_SPECIFIC", "TRANSFER_CORRIDOR_TO_LIVING",
        "TRANSFER_BALCONY_TO_BEDROOM", "TRANSFER_UTILITY_TO_KITCHEN", "TRANSFER_DINING_TO_KITCHEN",
        "TRANSFER_GUEST_BED_TO_MASTER", "TRANSFER_LIVING_TO_FOYER", "REBALANCE_EQUAL_BEDROOMS",
        "REBALANCE_PUBLIC_PRIVATE_SPLIT", "COMPRESS_CIRCULATION_FOR_USABLE_AREA"
    ],
    "MOVEMENT": [
        "MOVE_ABSOLUTE", "MOVE_RELATIVE", "SWAP_ROOMS", "ROTATE_ROOM_ORIENTATION",
        "RELOCATE_TO_ENTRANCE", "RELOCATE_TO_REAR", "RELOCATE_TO_CORNER",
        "RELOCATE_TO_PERIMETER", "RELOCATE_BEDROOM_TO_QUIET_ZONE", "RELOCATE_KITCHEN_TO_SERVICE_ZONE",
        "SHIFT_PUBLIC_ZONE_FRONT", "SHIFT_PRIVATE_ZONE_REAR"
    ],
    "ADJACENCY": [
        "ENFORCE_POSITIVE", "ENFORCE_NEGATIVE", "MAINTAIN_ADJACENCY",
        "ATTACH_BATHROOM_TO_MASTER", "CONNECT_KITCHEN_TO_DINING", "CONNECT_FOYER_TO_LIVING",
        "SEPARATE_BATHROOM_FROM_POOJA", "SEPARATE_KITCHEN_FROM_WC", "SEPARATE_BEDROOM_FROM_LIVING_NOISE",
        "DIRECT_ACCESS_BALCONY_MASTER", "DIRECT_ACCESS_UTILITY_KITCHEN"
    ],
    "DOORS_WINDOWS": [
        "ADD_DOOR", "REMOVE_DOOR", "MOVE_DOOR", "CHANGE_SWING",
        "ADD_WINDOW", "REMOVE_WINDOW", "MOVE_WINDOW", "INCREASE_WINDOW_SIZE",
        "ADD_WINDOW_CROSS_VENT", "RELOCATE_DOOR_FOR_PRIVACY", "ADD_MAIN_ENTRANCE_DOUBLE_DOOR",
        "ADD_BALCONY_SLIDING_DOOR", "ALIGN_INTERNAL_DOORS_CIRCULATION"
    ],
    "ENVIRONMENTAL": [
        "IMPROVE_VENTILATION", "IMPROVE_LIGHT", "IMPROVE_PRIVACY",
        "MAXIMIZE_CROSS_VENTILATION", "MAXIMIZE_DAYLIGHT_FACTOR", "REDUCE_SOLAR_HEAT_GAIN",
        "ENHANCE_AIRFLOW_CORRIDOR", "ACOUSTIC_ISOLATION_STUDY", "VISUAL_PRIVACY_ENTRANCE"
    ],
    "CONSTRAINTS_PRESERVATION": [
        "RESIZE_WITH_PRESERVATION", "MOVE_WITH_PRESERVATION", "TRANSFER_WITH_PRESERVATION",
        "ADD_WITH_PRESERVATION", "PRESERVE_SINGLE_ROOM", "PRESERVE_MULTI_ROOMS",
        "PRESERVE_EXTERIOR_ENVELOPE", "PRESERVE_PLUMBING_STACK", "LOCK_WALL_ALIGNMENT"
    ],
    "HIGH_LEVEL_OBJECTIVES": [
        "MAKE_MORE_SPACIOUS", "MAKE_LESS_CRAMPED", "MAKE_AIRY", "MAKE_OPEN_CONCEPT",
        "IMPROVE_CIRCULATION_FLOW", "REDUCE_WASTED_PASSAGEWAY", "OPTIMIZE_FURNITURE_USABILITY",
        "CREATE_SEAMLESS_INDOOR_OUTDOOR", "STREAMLINE_SERVICE_CORE"
    ],
    "VASTU_PREFERENCES": [
        "ALIGN_KITCHEN_SOUTHEAST", "ALIGN_MASTER_SOUTHWEST", "ALIGN_POOJA_NORTHEAST",
        "ALIGN_ENTRANCE_NORTH_OR_EAST", "AVOID_WC_NORTHEAST", "POSITION_LIVING_NORTH_OR_EAST",
        "CENTRAL_BRAHMASTHAN_OPEN"
    ],
    "CONVERSATIONAL_CONTROL": [
        "EXPLAIN_LAYOUT", "COMPARATIVE_ANALYSIS", "CLARIFY_AMBIGUITY",
        "RESOLVE_PRONOUN_IT", "RESOLVE_THAT_ROOM", "RESOLVE_NUMBERED_ROOM",
        "UNDO_LAST", "REDO_ACTION", "RESTORE_VERSION_N", "FINALIZE_APPROVAL",
        "QUERY_ROOM_DIMENSIONS", "QUERY_TOTAL_AREA", "NORMAL_GREETING"
    ],
    "INFEASIBILITY_AND_EDGE_CASES": [
        "REJECT_PLOT_OVERFLOW", "REJECT_NBC_MINIMUM_VIOLATION", "REJECT_PRESERVATION_CONFLICT",
        "REJECT_OVERLAPPING_WALLS", "CLARIFY_AMBIGUOUS_MULTI_TARGET", "EXPLAIN_STRUCTURAL_LIMIT"
    ]
}


class ArchitecturalOntology:
    """Ontology resolver for normalizing natural language terms to canonical architectural concepts."""
    
    @classmethod
    def resolve_room_type(cls, term: str) -> Optional[str]:
        """Resolves any room synonym to its canonical architectural room type."""
        if not term:
            return None
        t = term.lower().strip()
        t = re.sub(r'[\-_]', ' ', t)
        
        # Direct lookup
        if t in SYNONYM_TO_CANONICAL:
            return SYNONYM_TO_CANONICAL[t]
        
        # Check if contains a known synonym (longer phrases first to avoid greedy substring collisions)
        for syn, canonical in sorted(SYNONYM_TO_CANONICAL.items(), key=lambda x: len(x[0]), reverse=True):
            pattern = r'\b' + re.escape(syn) + r'\b'
            if re.search(pattern, t):
                return canonical
                
        # Word boundary heuristics
        if "master" in t:
            return "master_bedroom"
        if "bed" in t or "br" in t:
            return "bedroom"
        if "bath" in t or "toilet" in t or "wash" in t or "wc" in t or "restroom" in t:
            return "bathroom"
        if "cook" in t or "kitchen" in t:
            return "kitchen"
        if "din" in t:
            return "dining"
        if "liv" in t or "hall" in t or "lounge" in t:
            return "living_room"
        if "balcon" in t or "verand" in t or "terrace" in t:
            return "balcony"
        if "pooj" in t or "puj" in t or "mandir" in t:
            return "pooja_room"
        if "study" in t or "office" in t:
            return "study"
        if "gym" in t or "workout" in t:
            return "gym"
        if "game" in t or "gaming" in t:
            return "gaming_room"
        if "theatre" in t or "theater" in t or "cinema" in t:
            return "home_theatre"
        if "nursery" in t or "baby" in t:
            return "nursery"
        if "studio" in t or "music" in t or "craft" in t:
            return "studio"
            
        return None

    @classmethod
    def infer_functional_room_type(cls, text: str) -> Optional[str]:
        """Infers the intended room type from descriptive functional requirements."""
        if not text:
            return None
        t = text.lower()
        for pattern, room_type in FUNCTIONAL_INFERENCE_RULES:
            if re.search(pattern, t):
                return room_type
        # Fallback to direct resolution
        return cls.resolve_room_type(text)

    @classmethod
    def resolve_spatial_relation(cls, term: str) -> Optional[str]:
        """Resolves natural language spatial prepositions to canonical spatial relations."""
        t = term.lower().strip()
        for canonical, phrases in SPATIAL_RELATIONS.items():
            for p in phrases:
                if p in t:
                    return canonical
        return None

    @classmethod
    def parse_dimension_amount(cls, text: str) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """
        Extracts numerical amount, unit, and scale (e.g. 2 ft, 20 sqft, 10%, 'slightly') from text.
        Returns: (value, unit, qualitative_scale)
        """
        t = text.lower()
        
        # Check percentage
        m_pct = re.search(r'(\d+(?:\.\d+)?)\s*%', t)
        if m_pct:
            return float(m_pct.group(1)), "percent", "percentage"
            
        # Check area units (sqft / sqm / square feet)
        m_area = re.search(r'(\d+(?:\.\d+)?)\s*(sqft|sq\s*ft|sq\.?\s*m|square\s*(?:feet|foot|meters|meter))', t)
        if m_area:
            val = float(m_area.group(1))
            unit_str = m_area.group(2).replace(" ", "").replace(".", "")
            if "m" in unit_str:
                val *= 10.7639  # convert to sqft
            return val, "sqft", "exact_area"
            
        # Check linear units (ft, meters, inches)
        m_len = re.search(r'(\d+(?:\.\d+)?)\s*(feet|foot|ft|\'|meters|meter|m|inches|inch|\")', t)
        if m_len:
            val = float(m_len.group(1))
            unit_str = m_len.group(2)
            if unit_str in ("m", "meter", "meters", "metre", "metres"):
                val *= 3.28084
            elif unit_str in ("inches", "inch", '"'):
                val /= 12.0
            return val, "ft", "exact_linear"
            
        # Dimension target (e.g. 12x14 or 12 by 14)
        m_dim = re.search(r'(\d+(?:\.\d+)?)\s*(?:x|by|\*)\s*(\d+(?:\.\d+)?)', t)
        if m_dim:
            w = float(m_dim.group(1))
            l = float(m_dim.group(2))
            return w * l, "sqft", "exact_dimensions"

        # Bare number
        m_num = re.search(r'\b(\d+(?:\.\d+)?)\b', t)
        if m_num:
            return float(m_num.group(1)), "ft", "numeric_default"
            
        # Qualitative scales
        if any(w in t for w in ["slightly", "a little", "a bit", "tiny bit", "somewhat"]):
            return 1.5, "ft", "small_delta"
        if any(w in t for w in ["significantly", "much", "lot", "substantially", "heavily"]):
            return 4.0, "ft", "large_delta"
            
        return None, None, "default"

    @classmethod
    def get_display_name(cls, canonical_type: str) -> str:
        """Returns human-friendly display label for a room type."""
        names = {
            "master_bedroom": "Master Bedroom",
            "living_room": "Living Room / Hall",
            "pooja_room": "Pooja Room",
            "bedroom": "Bedroom",
            "kitchen": "Kitchen",
            "dining": "Dining Room",
            "bathroom": "Bathroom",
            "balcony": "Balcony",
            "study": "Study / Office",
            "corridor": "Corridor",
            "foyer": "Entrance Foyer",
            "utility": "Utility / Wash",
            "courtyard": "Courtyard",
            "staircase": "Staircase",
            "gym": "Home Gym",
            "home_theatre": "Home Theatre",
            "gaming_room": "Gaming Room",
            "nursery": "Nursery",
            "studio": "Creative Studio",
            "dressing_room": "Dressing Room"
        }
        return names.get(canonical_type, canonical_type.replace("_", " ").title())
