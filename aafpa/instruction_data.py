"""
AAFPA 2.0 Architectural Instruction Dataset Generator
Generates diverse, realistic multi-turn conversational datasets mapping
natural language instructions to structured architectural actions for training and evaluation.
"""

import json
import random
from typing import List, Dict, Any, Tuple

ROOM_SYNONYMS = {
    "master_bedroom": ["master bedroom", "master bed", "primary bedroom", "main bedroom", "master room"],
    "bedroom": ["bedroom", "bedroom 2", "second bedroom", "guest bedroom", "kids room", "bed room"],
    "bathroom": ["bathroom", "washroom", "toilet", "restroom", "attached bath", "common bathroom", "powder room"],
    "kitchen": ["kitchen", "modular kitchen", "cooking space", "pantry", "cooking area"],
    "living_room": ["living room", "living hall", "drawing room", "hall", "lounge", "family room"],
    "dining": ["dining room", "dining area", "eating space", "dining hall"],
    "balcony": ["balcony", "verandah", "terrace", "patio", "deck"],
    "study": ["study room", "study", "home office", "work room", "office"],
    "pooja_room": ["pooja room", "pooja altar", "prayer room", "mandir", "puja space"]
}

RESIZE_TEMPLATES = [
    ("Make {room} {amount} bigger.", "RESIZE_ROOM", "increase"),
    ("Enlarge the {room} by {amount}.", "RESIZE_ROOM", "increase"),
    ("Can you make {room} more spacious?", "RESIZE_ROOM", "increase"),
    ("Give {room} another {amount}.", "RESIZE_ROOM", "increase"),
    ("Expand {room} slightly.", "RESIZE_ROOM", "increase"),
    ("Reduce {room} by {amount}.", "RESIZE_ROOM", "decrease"),
    ("Make {room} smaller.", "RESIZE_ROOM", "decrease"),
    ("Shrink the {room} a little.", "RESIZE_ROOM", "decrease"),
    ("Decrease {room} size.", "RESIZE_ROOM", "decrease")
]

WIDTH_LENGTH_TEMPLATES = [
    ("Make {room} {amount} wider.", "CHANGE_WIDTH", "increase"),
    ("Increase the width of {room} by {amount}.", "CHANGE_WIDTH", "increase"),
    ("Make {room} narrower.", "CHANGE_WIDTH", "decrease"),
    ("Make {room} longer instead of wider.", "CHANGE_LENGTH", "increase"),
    ("Increase the depth of {room}.", "CHANGE_LENGTH", "increase"),
    ("Shorten the length of {room}.", "CHANGE_LENGTH", "decrease")
]

TRANSFER_TEMPLATES = [
    ("Take {amount} from {source} and give it to {target}.", "TRANSFER_AREA"),
    ("Reduce {source} and use that extra space for {target}.", "TRANSFER_AREA"),
    ("Steal some space from {source} for {target}.", "TRANSFER_AREA"),
    ("Transfer area from {source} into {target}.", "TRANSFER_AREA")
]

SWAP_REPLACE_TEMPLATES = [
    ("Replace the {source} with a {target}.", "REPLACE_ROOM"),
    ("Convert the {source} into a {target}.", "REPLACE_ROOM"),
    ("Turn {source} into an {target}.", "REPLACE_ROOM"),
    ("Swap {source} and {target}.", "SWAP_ROOMS"),
    ("Interchange the positions of {source} and {target}.", "SWAP_ROOMS")
]

SPATIAL_MOVE_TEMPLATES = [
    ("Move the {target} beside the {anchor}.", "MOVE_ROOM", "beside"),
    ("Shift {target} next to {anchor}.", "MOVE_ROOM", "beside"),
    ("Put {target} above the {anchor}.", "MOVE_ROOM", "above"),
    ("Move {target} to the right of {anchor}.", "MOVE_ROOM", "right")
]

class ArchitecturalInstructionDataset:
    """Dataset synthesizer for natural language to architectural action mapping."""

    @classmethod
    def generate_instruction_samples(cls, num_samples: int = 200) -> List[Dict[str, Any]]:
        """Generates diverse synthetic instruction-action pairs."""
        dataset = []
        units = ["2 ft", "3 ft", "20 sqft", "30 sqft", "10%", "a little", "2 feet"]

        for _ in range(num_samples):
            choice = random.choice(["resize", "width_len", "transfer", "swap_replace", "move", "multi_step"])

            if choice == "resize":
                tmpl, action, direction = random.choice(RESIZE_TEMPLATES)
                rtype = random.choice(list(ROOM_SYNONYMS.keys()))
                syn = random.choice(ROOM_SYNONYMS[rtype])
                amt = random.choice(units)
                text = tmpl.format(room=syn, amount=amt)
                dataset.append({
                    "instruction": text,
                    "target_canonical": rtype,
                    "operation": action,
                    "direction": direction,
                    "category": "resize"
                })

            elif choice == "width_len":
                tmpl, action, direction = random.choice(WIDTH_LENGTH_TEMPLATES)
                rtype = random.choice(list(ROOM_SYNONYMS.keys()))
                syn = random.choice(ROOM_SYNONYMS[rtype])
                amt = random.choice(units)
                text = tmpl.format(room=syn, amount=amt)
                dataset.append({
                    "instruction": text,
                    "target_canonical": rtype,
                    "operation": action,
                    "direction": direction,
                    "category": "dimensional"
                })

            elif choice == "transfer":
                tmpl, action = random.choice(TRANSFER_TEMPLATES)
                src_type, tgt_type = random.sample(list(ROOM_SYNONYMS.keys()), 2)
                src_syn = random.choice(ROOM_SYNONYMS[src_type])
                tgt_syn = random.choice(ROOM_SYNONYMS[tgt_type])
                amt = random.choice(["20 sqft", "30 sqft", "some space", "15 sqft"])
                text = tmpl.format(source=src_syn, target=tgt_syn, amount=amt)
                dataset.append({
                    "instruction": text,
                    "source_canonical": src_type,
                    "target_canonical": tgt_type,
                    "operation": action,
                    "category": "area_transfer"
                })

            elif choice == "swap_replace":
                tmpl, action = random.choice(SWAP_REPLACE_TEMPLATES)
                src_type, tgt_type = random.sample(list(ROOM_SYNONYMS.keys()), 2)
                src_syn = random.choice(ROOM_SYNONYMS[src_type])
                tgt_syn = random.choice(ROOM_SYNONYMS[tgt_type])
                text = tmpl.format(source=src_syn, target=tgt_syn)
                dataset.append({
                    "instruction": text,
                    "target_canonical": src_type,       # Old room to replace
                    "replacement_canonical": tgt_type,  # New replacement room
                    "operation": action,
                    "category": "topology_mutation"
                })

            elif choice == "move":
                tmpl, action, rel = random.choice(SPATIAL_MOVE_TEMPLATES)
                tgt_type, anc_type = random.sample(list(ROOM_SYNONYMS.keys()), 2)
                tgt_syn = random.choice(ROOM_SYNONYMS[tgt_type])
                anc_syn = random.choice(ROOM_SYNONYMS[anc_type])
                text = tmpl.format(target=tgt_syn, anchor=anc_syn)
                dataset.append({
                    "instruction": text,
                    "target_canonical": tgt_type,
                    "anchor_canonical": anc_type,
                    "operation": action,
                    "spatial_relation": rel,
                    "category": "spatial_move"
                })

            elif choice == "multi_step":
                text = "Remove the balcony and make the master bedroom 2 feet wider."
                dataset.append({
                    "instruction": text,
                    "operation": "MULTI_STEP",
                    "operations_count": 2,
                    "category": "multi_step"
                })

        return dataset

    @classmethod
    def save_dataset_splits(cls, filepath: str = "architectural_instructions_eval.json"):
        """Saves generated synthetic evaluation dataset to JSON."""
        data = cls.generate_instruction_samples(300)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return filepath
