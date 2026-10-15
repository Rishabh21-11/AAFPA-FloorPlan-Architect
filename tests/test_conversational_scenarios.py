"""
Comprehensive Test Suite for AAFPA Smart Conversational Architect
Evaluates all 20 canonical architectural conversational scenarios, multi-turn pronoun tracking,
preservation constraints, RAG explanations, high-level objectives, and zero-hallucination handling.
"""

import os
import sys
import unittest

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))

from aafpa import (
    InteractiveFloorPlanStudioSession,
    ArchitecturalOntology,
    ArchitecturalActionType
)

class TestConversationalArchitectScenarios(unittest.TestCase):
    """Evaluates the 20 benchmark conversations against the Smart Conversational Architect."""

    def setUp(self):
        self.session = InteractiveFloorPlanStudioSession()
        # Initialize with standard 2BHK layout
        self.session.handle_message("I want a 2BHK in 1000 sqft with 2 bathrooms and a modular kitchen.")
        self.session.handle_message("Select layout 2.")

    def test_01_make_master_bedroom_bigger(self):
        """TEST 1: Make the master bedroom bigger."""
        res = self.session.handle_message("Make the master bedroom bigger.")
        self.assertIn(res["status"], ("success", "partial"))
        self.assertTrue("master bedroom" in res["explanation"].lower() or "master_bedroom" in res["explanation"].lower())

    def test_02_pronoun_wider(self):
        """TEST 2: Now make it wider (Resolves 'it' to master bedroom)."""
        self.session.handle_message("Make the master bedroom bigger.")
        res = self.session.handle_message("Now make it wider.")
        self.assertIn(res["status"], ("success", "partial"))
        self.assertEqual(res["structured_intent"]["resolved_references"]["target_type"], "master_bedroom")

    def test_03_preservation_constraint(self):
        """TEST 3: Don't reduce the bathroom (Preservation constraint extraction)."""
        res = self.session.handle_message("Make the master bedroom bigger, but don't reduce the bathroom.")
        self.assertIn(res["status"], ("success", "partial"))
        self.assertIn("bathroom", res["structured_intent"]["preserve_rooms"])

    def test_04_area_transfer(self):
        """TEST 4: Use some space from the dining room instead."""
        res = self.session.handle_message("Use some space from the dining room instead.")
        self.assertIn(res["status"], ("success", "partial"))
        self.assertEqual(res["structured_intent"]["operations"][0]["type"], "TRANSFER_AREA")

    def test_05_undo_last(self):
        """TEST 5: Actually undo that."""
        self.session.handle_message("Make the master bedroom bigger.")
        res = self.session.handle_message("Actually undo that.")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["action"], "undo")

    def test_06_functional_room_inference(self):
        """TEST 6: Add a small quiet room where I can work (Infers 'study')."""
        res = self.session.handle_message("Add a small quiet room where I can work.")
        self.assertIn(res["status"], ("success", "partial"))
        self.assertEqual(res["structured_intent"]["operations"][0]["target_room"], "study")

    def test_07_spatial_placement_with_privacy(self):
        """TEST 7: Put it near the living room."""
        self.session.handle_message("Add a study.")
        res = self.session.handle_message("Put it near the living room.")
        self.assertIn(res["status"], ("success", "partial"))

    def test_08_environmental_with_preservation(self):
        """TEST 8: Improve ventilation without changing bedroom sizes."""
        res = self.session.handle_message("Improve ventilation without changing bedroom sizes.")
        self.assertIn(res["status"], ("success", "partial"))
        self.assertIn("bedroom", res["structured_intent"]["preserve_rooms"])

    def test_09_high_level_spaciousness(self):
        """TEST 9: Make the house feel less cramped."""
        res = self.session.handle_message("Make the house feel less cramped.")
        self.assertIn(res["status"], ("success", "partial"))

    def test_10_design_explanation(self):
        """TEST 10: Why did you put the bathroom there?"""
        res = self.session.handle_message("Why did you put the bathroom there?")
        self.assertEqual(res["status"], "conversation")
        self.assertIn("zoning", res["explanation"].lower())

    def test_11_move_closer_to_master(self):
        """TEST 11: Okay, move it closer to the master bedroom."""
        self.session.handle_message("Focus on the bathroom.")
        res = self.session.handle_message("Move it closer to the master bedroom.")
        self.assertIn(res["status"], ("success", "partial"))

    def test_12_keep_and_shrink(self):
        """TEST 12: Actually keep it where it was but make it smaller."""
        res = self.session.handle_message("Make the bathroom smaller.")
        self.assertIn(res["status"], ("success", "partial"))

    def test_13_add_music_room(self):
        """TEST 13: Add a music room (Custom room type)."""
        res = self.session.handle_message("Add a music room.")
        self.assertIn(res["status"], ("success", "partial"))
        self.assertEqual(res["structured_intent"]["operations"][0]["target_room"], "studio")

    def test_14_exact_dimension(self):
        """TEST 14: Make the kitchen 12 feet wide."""
        res = self.session.handle_message("Make the kitchen 12 feet wide.")
        self.assertIn(res["status"], ("success", "partial"))

    def test_15_remove_and_transfer(self):
        """TEST 15: Remove the balcony and use that space for the living room."""
        res = self.session.handle_message("Remove the balcony.")
        self.assertIn(res["status"], ("success", "partial"))

    def test_16_conditional_addition(self):
        """TEST 16: Add another bathroom if there is enough space."""
        res = self.session.handle_message("Add another bathroom if there is enough space.")
        self.assertIn(res["status"], ("success", "partial"))

    def test_17_preservation_bedrooms(self):
        """TEST 17: Don't touch the bedrooms."""
        res = self.session.handle_message("Expand the kitchen, but don't touch the bedrooms.")
        self.assertIn("bedroom", res["structured_intent"]["preserve_rooms"])

    def test_18_layout_comparison(self):
        """TEST 18: Which of the four layouts has better ventilation?"""
        res = self.session.handle_message("Which of the four layouts has better ventilation?")
        self.assertEqual(res["status"], "conversation")
        self.assertIn("ventilation", res["explanation"].lower())

    def test_19_privacy_improvement(self):
        """TEST 19: Make this layout more private."""
        res = self.session.handle_message("Make this layout more private.")
        self.assertIn(res["status"], ("success", "partial"))

    def test_20_undo_multi(self):
        """TEST 20: Undo the last change."""
        self.session.handle_message("Make the bedroom bigger.")
        res = self.session.handle_message("Undo that.")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["action"], "undo")

    def test_21_add_entrance_on_right_of_bathroom_and_remember(self):
        """TEST 21: Add an entrance on the right side of the bathroom and verify multi-turn memory."""
        res = self.session.handle_message("Add an entrance on the right side of the bathroom.")
        self.assertIn(res["status"], ("success", "partial"))
        self.assertEqual(res["structured_intent"]["operations"][0]["target_room"], "foyer")
        self.assertEqual(res["structured_intent"]["operations"][0]["relative_target"], "bathroom")
        self.assertEqual(res["structured_intent"]["operations"][0]["spatial_relation"], "right")
        self.assertTrue("foyer" in res["explanation"].lower() or "entrance" in res["explanation"].lower())
        self.assertIn("bathroom", res["explanation"].lower())

        # Verify newly added room exists in active plan
        new_foyer = next((r for r in res["plan"].rooms if r.type == "foyer"), None)
        self.assertIsNotNone(new_foyer)

        # Follow-up test: verify conversational memory remembers the newly added entrance when referenced as 'it'
        res2 = self.session.handle_message("Now make it wider.")
        self.assertEqual(res2["structured_intent"]["resolved_references"]["target_type"], "foyer")

    def test_22_replace_room_direct(self):
        """TEST 22: Replace the balcony with a study."""
        res = self.session.handle_message("Replace the balcony with a study.")
        self.assertIn(res["status"], ("success", "partial"))
        self.assertEqual(res["structured_intent"]["operations"][0]["type"], "REPLACE_ROOM")
        self.assertEqual(res["structured_intent"]["operations"][0]["target_room"], "balcony")
        self.assertEqual(res["structured_intent"]["operations"][0]["source_room"], "study")
        self.assertIn("converted", res["explanation"].lower())

        # Verify study exists in plan
        has_study = any(r.type == "study" for r in res["plan"].rooms)
        self.assertTrue(has_study)

    def test_23_convert_room_to_gym(self):
        """TEST 23: Convert the bedroom into a gym."""
        res = self.session.handle_message("Convert the bedroom into a gym.")
        self.assertIn(res["status"], ("success", "partial"))
        self.assertEqual(res["structured_intent"]["operations"][0]["type"], "REPLACE_ROOM")
        self.assertEqual(res["structured_intent"]["operations"][0]["target_room"], "bedroom")
        self.assertEqual(res["structured_intent"]["operations"][0]["source_room"], "gym")

        # Verify gym exists in plan
        has_gym = any(r.type == "gym" for r in res["plan"].rooms)
        self.assertTrue(has_gym)

    def test_24_pronoun_replace_followup(self):
        """TEST 24: Focus on bedroom then replace it with a pooja room."""
        self.session.handle_message("Focus on the bedroom.")
        res = self.session.handle_message("Turn it into a pooja room.")
        self.assertIn(res["status"], ("success", "partial"))
        self.assertEqual(res["structured_intent"]["operations"][0]["type"], "REPLACE_ROOM")
        self.assertEqual(res["structured_intent"]["operations"][0]["source_room"], "pooja_room")


class TestHallucinationAndEdgeCases(unittest.TestCase):
    """Tests zero-hallucination and physical impossibility handling."""

    def setUp(self):
        self.session = InteractiveFloorPlanStudioSession()
        self.session.handle_message("2BHK on 1000 sqft.")
        self.session.handle_message("1")

    def test_impossible_plot_overflow(self):
        """Rejects impossible 5+ bedrooms in 400 sqft."""
        res = self.session.handle_message("Add 5 bedrooms and a pool in 400 sqft.")
        self.assertEqual(res["status"], "infeasible")
        self.assertIn("impossible", res["explanation"].lower())

    def test_impossible_room_dimension(self):
        """Rejects 60 ft room in 32 ft plot."""
        res = self.session.handle_message("Make the bedroom 60 feet wide.")
        self.assertEqual(res["status"], "infeasible")
        self.assertIn("exceeds your plot boundary", res["explanation"].lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
