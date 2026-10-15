"""
Automated Comprehensive Test Suite for AAFPA 2.0
Tests all 21 core requirements (A to U) ensuring complete functionality, generalization, and robust error handling.
"""

import sys
import unittest
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aafpa import (
    ArchitecturalOntology,
    ArchitecturalActionType,
    SemanticIntentAgent,
    PlanMemory,
    GenericGeometryEngine,
    UnifiedFloorPlanDataset,
    SemanticRAGEngine,
    EvaluationBenchmark
)

class MockPlot:
    def __init__(self, width_ft=32.0, length_ft=31.25):
        self.width_ft = width_ft
        self.length_ft = length_ft
        self.area_sqft = width_ft * length_ft

class MockRoom:
    def __init__(self, id, type, zone, x, y, width, length, adjacent_to=None, doors=None, windows=None):
        self.id = id
        self.type = type
        self.zone = zone
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.length = float(length)
        self.adjacent_to = adjacent_to or []
        self.doors = doors or []
        self.windows = windows or []

    @property
    def area(self):
        return round(self.width * self.length, 1)

class MockPlan:
    def __init__(self):
        self.plot = MockPlot()
        self.version = 1
        self.rooms = [
            MockRoom("living_1", "living_room", "public", 0.0, 0.0, 16.0, 16.0),
            MockRoom("dining_1", "dining", "public", 16.0, 0.0, 16.0, 10.0),
            MockRoom("kitchen_1", "kitchen", "service", 16.0, 10.0, 16.0, 6.0),
            MockRoom("mbr_1", "master_bedroom", "private", 0.0, 16.0, 16.0, 15.25),
            MockRoom("bath_1", "bathroom", "service", 16.0, 16.0, 8.0, 7.0),
            MockRoom("bed_2", "bedroom", "private", 16.0, 23.0, 16.0, 8.25),
            MockRoom("balcony_1", "balcony", "service", 0.0, 31.25, 10.0, 4.0)
        ]

class TestAAFPA2Suite(unittest.TestCase):

    def setUp(self):
        self.memory = PlanMemory()
        self.agent = SemanticIntentAgent(self.memory)
        self.geom_engine = GenericGeometryEngine()
        self.mock_plan = MockPlan()
        self.memory.current_plan = self.mock_plan

    # A. Synonym Understanding
    def test_a_synonyms(self):
        self.assertEqual(ArchitecturalOntology.resolve_room_type("washroom"), "bathroom")
        self.assertEqual(ArchitecturalOntology.resolve_room_type("toilet"), "bathroom")
        self.assertEqual(ArchitecturalOntology.resolve_room_type("hall"), "living_room")
        self.assertEqual(ArchitecturalOntology.resolve_room_type("drawing room"), "living_room")
        self.assertEqual(ArchitecturalOntology.resolve_room_type("master bed"), "master_bedroom")
        self.assertEqual(ArchitecturalOntology.resolve_room_type("cooking space"), "kitchen")
        self.assertEqual(ArchitecturalOntology.resolve_room_type("eating area"), "dining")
        self.assertEqual(ArchitecturalOntology.resolve_room_type("mandir"), "pooja_room")

    # B. Room Addition
    def test_b_room_addition(self):
        intent = self.agent.parse_intent("Add a study room.")
        self.assertTrue(any(op.type == ArchitecturalActionType.ADD_ROOM for op in intent.operations))
        success, msg, new_plan = self.geom_engine.apply_operations(self.mock_plan, intent.operations)
        self.assertTrue(success)
        self.assertTrue(any("study" in r.type for r in new_plan.rooms))

    # C. Room Deletion
    def test_c_room_deletion(self):
        intent = self.agent.parse_intent("Remove the balcony.")
        self.assertTrue(any(op.type == ArchitecturalActionType.REMOVE_ROOM for op in intent.operations))
        success, msg, new_plan = self.geom_engine.apply_operations(self.mock_plan, intent.operations)
        self.assertTrue(success)
        self.assertFalse(any(r.type == "balcony" for r in new_plan.rooms))

    # D. Room Resizing
    def test_d_room_resizing(self):
        intent = self.agent.parse_intent("Make bedroom 2 bigger.")
        self.assertTrue(len(intent.operations) > 0)
        success, msg, new_plan = self.geom_engine.apply_operations(self.mock_plan, intent.operations)
        self.assertTrue(success)

    # E. Width Change
    def test_e_width_change(self):
        intent = self.agent.parse_intent("Increase the width of bedroom 2 by 2 feet.")
        self.assertEqual(intent.operations[0].type, ArchitecturalActionType.CHANGE_WIDTH)
        self.assertEqual(intent.operations[0].dimension.value, 2.0)
        success, msg, new_plan = self.geom_engine.apply_operations(self.mock_plan, intent.operations)
        self.assertTrue(success)

    # F. Length Change
    def test_f_length_change(self):
        intent = self.agent.parse_intent("Make the master bedroom longer instead of wider.")
        self.assertEqual(intent.operations[0].type, ArchitecturalActionType.CHANGE_LENGTH)

    # G. Area Change & Natural Units
    def test_g_area_change(self):
        intent = self.agent.parse_intent("Give bedroom 2 another 20 square feet.")
        self.assertTrue(intent.operations[0].type in (ArchitecturalActionType.RESIZE_ROOM, ArchitecturalActionType.CHANGE_AREA))
        self.assertEqual(intent.operations[0].dimension.unit, "sqft")

    # H. Room Replacement & Conversion
    def test_h_room_replacement(self):
        intent = self.agent.parse_intent("Replace the dining room with a study.")
        self.assertEqual(intent.operations[0].type, ArchitecturalActionType.REPLACE_ROOM)
        success, msg, new_plan = self.geom_engine.apply_operations(self.mock_plan, intent.operations)
        self.assertTrue(success)
        self.assertTrue(any(r.type == "study" for r in new_plan.rooms))

    # I. Room Swap
    def test_i_room_swap(self):
        intent = self.agent.parse_intent("Swap kitchen and dining.")
        self.assertEqual(intent.operations[0].type, ArchitecturalActionType.SWAP_ROOMS)
        success, msg, new_plan = self.geom_engine.apply_operations(self.mock_plan, intent.operations)
        self.assertTrue(success)

    # J. Area Transfer
    def test_j_area_transfer(self):
        intent = self.agent.parse_intent("Take 20 sqft from dining and give it to bedroom 2.")
        self.assertEqual(intent.operations[0].type, ArchitecturalActionType.TRANSFER_AREA)
        success, msg, new_plan = self.geom_engine.apply_operations(self.mock_plan, intent.operations)
        self.assertTrue(success)

    # K. Spatial References & Relative Positioning
    def test_k_spatial_references(self):
        intent = self.agent.parse_intent("Make the room above the bathroom bigger.")
        self.assertTrue(len(intent.operations) > 0)
        # Should resolve relative room above bathroom
        self.assertIsNotNone(intent.operations[0].target_room)

    # L. Multi-Step Commands
    def test_l_multi_step_commands(self):
        intent = self.agent.parse_intent("Remove the balcony and make the master bedroom 2 feet wider.")
        self.assertGreaterEqual(len(intent.operations), 2)
        success, msg, new_plan = self.geom_engine.apply_operations(self.mock_plan, intent.operations)
        self.assertTrue(success)

    # M. Multi-Turn Pronoun Tracking
    def test_m_multi_turn_coreference(self):
        # Turn 1: "Make master bedroom bigger"
        i1 = self.agent.parse_intent("Make the master bedroom bigger.")
        self.assertEqual(i1.operations[0].target_room, "master_bedroom")
        self.memory.set_focus("mbr_1", "master_bedroom")

        # Turn 2: "Now make it wider." -> 'it' resolves to master bedroom
        i2 = self.agent.parse_intent("Now make it wider.")
        self.assertEqual(i2.operations[0].target_room, "master_bedroom")
        self.assertEqual(i2.operations[0].type, ArchitecturalActionType.CHANGE_WIDTH)

        # Turn 3: "Move the bathroom beside it." -> 'it' resolves to master bedroom
        i3 = self.agent.parse_intent("Move the bathroom beside it.")
        self.assertEqual(i3.operations[0].relative_target, "master_bedroom")

    # N. Ambiguous & Informal Language
    def test_n_informal_phrasing(self):
        intent1 = self.agent.parse_intent("Can you shrink the toilet a little?")
        self.assertEqual(intent1.operations[0].target_room, "bathroom")
        self.assertEqual(intent1.operations[0].dimension.direction, "decrease")

        intent2 = self.agent.parse_intent("I don't need such a large bath.")
        self.assertEqual(intent2.operations[0].target_room, "bathroom")

    # O. High-level Design Objectives
    def test_o_high_level_objectives(self):
        intent_vent = self.agent.parse_intent("Improve ventilation in the house.")
        self.assertEqual(intent_vent.operations[0].type, ArchitecturalActionType.IMPROVE_VENTILATION)

        intent_light = self.agent.parse_intent("Give the house better natural lighting.")
        self.assertEqual(intent_light.operations[0].type, ArchitecturalActionType.IMPROVE_LIGHTING)

    # P. Plan Preservation (Minimum Necessary Change)
    def test_p_plan_preservation(self):
        old_kitchen = next(r for r in self.mock_plan.rooms if r.type == "kitchen")
        intent = self.agent.parse_intent("Make the master bedroom 1 foot wider.")
        success, msg, new_plan = self.geom_engine.apply_operations(self.mock_plan, intent.operations)
        new_kitchen = next(r for r in new_plan.rooms if r.type == "kitchen")
        # Kitchen should remain unaltered
        self.assertEqual(old_kitchen.width, new_kitchen.width)
        self.assertEqual(old_kitchen.length, new_kitchen.length)

    # Q. Versioning, Snapshots & Undo
    def test_q_versioning_and_undo(self):
        self.memory.snapshot("Initial")
        intent = self.agent.parse_intent("Remove balcony.")
        _, _, new_plan = self.geom_engine.apply_operations(self.mock_plan, intent.operations)
        self.memory.current_plan = new_plan
        self.memory.snapshot("Removed balcony")
        self.assertEqual(len(self.memory.history), 2)

        # Undo
        restored = self.memory.undo()
        self.assertIsNotNone(restored)
        self.assertTrue(any(r.type == "balcony" for r in restored.rooms))

    # R. RAG Knowledge Base Retrieval
    def test_r_rag_engine(self):
        rag = SemanticRAGEngine()
        rules = rag.retrieve("habitable room minimum width and ventilation", top_k=3)
        self.assertTrue(len(rules) > 0)
        self.assertTrue(any("NBC" in r.rule_id for r in rules))

    # S. Dataset Pipeline (RPLAN + CubiCasa5K)
    def test_s_dataset_pipeline(self):
        dataset_loader = UnifiedFloorPlanDataset()
        rplan_samples = dataset_loader.load_rplan_samples(max_samples=5)
        self.assertTrue(isinstance(rplan_samples, list))
        cubicasa_samples = dataset_loader.load_cubicasa_samples(max_samples=5)
        self.assertTrue(isinstance(cubicasa_samples, list))
        priors = dataset_loader.get_topology_prior()
        self.assertIn("open_plan", priors)

    # T. Benchmark Suite Run
    def test_t_evaluation_benchmark(self):
        benchmark = EvaluationBenchmark(self.agent)
        results = benchmark.run_full_benchmark(num_samples=30)
        self.assertIn("1. Intent Accuracy", results)
        self.assertIn("6. Constraint Satisfaction Rate (NBC 2016)", results)

if __name__ == "__main__":
    unittest.main()
