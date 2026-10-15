"""
AAFPA 2.0 Smart Agent Smoke Test
Verifies:
1. HouseMind dataset loads correctly and returns condition-action pairs
2. ConditionGroundedSmartAgent produces different actions for the same utterance
   on different plan states (the core condition-grounding requirement)
3. ArchitectEngineFacade tool calls work and validate correctly
4. Full conversational loop runs (describe -> 4 layouts -> select -> edit -> undo)
"""

import sys, os
sys.path.insert(0, os.path.abspath("."))

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

# -------------------------------------------------------------------------
# Test 1: HouseMind Dataset
# -------------------------------------------------------------------------
section("TEST 1: HouseMind Dataset Loader")

from aafpa.dataset_pipeline import HouseMindDatasetLoader

loader = HouseMindDatasetLoader("data_test.zip")
stats = loader.get_stats()
print(f"Understanding samples : {stats['understanding_samples']}")
print(f"Editing samples       : {stats['editing_samples']}")
print(f"Generation samples    : {stats['generation_samples']}")
print(f"Condition-action pairs: {stats['condition_action_pairs']}")
print(f"Top room types        : {list(stats['room_distribution'].items())[:5]}")
print(f"Spatial relations     : {list(stats['spatial_edge_distribution'].items())[:5]}")

pairs = loader.build_condition_action_pairs()
print(f"\nSample condition-action pair:")
if pairs:
    p = pairs[0]
    print(f"  house_id: {p['house_id']}")
    print(f"  instruction: {p['user_instruction']}")
    plan_rooms = p['plan_state']['rooms']
    print(f"  plan rooms: {[r['type'] for r in plan_rooms]}")

# -------------------------------------------------------------------------
# Test 2: Condition-Grounded Agent — same utterance, different plan states
# -------------------------------------------------------------------------
section("TEST 2: Condition-Grounded Reasoning (Same Input, Different Plans)")

from aafpa.smart_agent import ConditionGroundedSmartAgent

# Build two mock plan states
class MockRoom:
    def __init__(self, id, type, x, y, w, l):
        self.id = id; self.type = type
        self.x = x; self.y = y
        self.width = w; self.length = l
        self.area = w * l
        self.windows = []

class MockPlot:
    def __init__(self): self.width_ft = 32.0; self.length_ft = 31.25

class MockPlan:
    def __init__(self):
        self.rooms = []; self.plot = MockPlot(); self.version = 1

# Plan A: has a large corridor (10 ft x 31 ft = ~310 sqft excess)
plan_a = MockPlan()
plan_a.rooms = [
    MockRoom("living_1",  "living_room",    0.0,  0.0, 14.0, 16.0),
    MockRoom("corridor_1","corridor",       14.0,  0.0,  8.0, 31.25),
    MockRoom("mbr_1",     "master_bedroom", 22.0,  0.0, 10.0, 15.0),
    MockRoom("bed_2",     "bedroom",        22.0, 15.0, 10.0, 16.25),
    MockRoom("kitchen_1", "kitchen",         0.0, 16.0, 14.0,  8.0),
    MockRoom("bath_1",    "bathroom",        0.0, 24.0, 14.0,  7.25),
]

# Plan B: NO corridor, but living and dining are separated
plan_b = MockPlan()
plan_b.rooms = [
    MockRoom("living_1",  "living_room",    0.0,  0.0, 14.0, 14.0),
    MockRoom("dining_1",  "dining",         14.0,  0.0, 14.0,  8.0),
    MockRoom("kitchen_1", "kitchen",        28.0,  0.0,  4.0, 14.0),
    MockRoom("mbr_1",     "master_bedroom",  0.0, 14.0, 14.0, 17.25),
    MockRoom("bed_2",     "bedroom",        14.0,  8.0, 18.0, 23.25),
    MockRoom("bath_1",    "bathroom",       14.0,  8.0,  8.0,  8.0),
]

agent_a = ConditionGroundedSmartAgent()
agent_b = ConditionGroundedSmartAgent()

utterance = "Make the house feel more spacious."
intent_a = agent_a.parse_intent(utterance, plan_a)
intent_b = agent_b.parse_intent(utterance, plan_b)

print(f"Utterance: '{utterance}'")
print(f"\nPlan A (large corridor {8*31.25:.0f} sqft):")
if intent_a.operations:
    op = intent_a.operations[0]
    print(f"  -> Action: {op.type.value}")
    print(f"  -> Source: {op.source_room} | Target: {op.target_room}")
    diag = op.parameters.get("diagnosis", "")
    print(f"  -> Diagnosis: {diag[:100]}")
else:
    print("  -> No operations generated")

print(f"\nPlan B (compartmentalized living/dining):")
if intent_b.operations:
    op = intent_b.operations[0]
    print(f"  -> Action: {op.type.value}")
    print(f"  -> Source: {op.source_room} | Target: {op.target_room}")
    diag = op.parameters.get("diagnosis", "")
    print(f"  -> Diagnosis: {diag[:100]}")
else:
    print("  -> No operations generated")

same_action = (
    intent_a.operations and intent_b.operations and
    intent_a.operations[0].type == intent_b.operations[0].type and
    intent_a.operations[0].source_room == intent_b.operations[0].source_room
)
print(f"\nDifferent actions for same utterance: {'YES (PASS)' if not same_action else 'NO (FAIL - still condition-blind)'}")

# -------------------------------------------------------------------------
# Test 3: Discourse Entity Stack (pronoun resolution)
# -------------------------------------------------------------------------
section("TEST 3: Discourse Entity Stack — Pronoun Resolution")

agent = ConditionGroundedSmartAgent()
agent.memory.current_plan = plan_a

t1 = agent.parse_intent("Make the master bedroom bigger.", plan_a)
print(f"Turn 1: 'Make the master bedroom bigger.'")
print(f"  -> {t1.operations[0].type.value if t1.operations else 'none'} | target: {t1.operations[0].target_room if t1.operations else 'none'}")

t2 = agent.parse_intent("Now make it wider instead of longer.", plan_a)
print(f"Turn 2: 'Now make it wider instead of longer.'")
print(f"  -> {t2.operations[0].type.value if t2.operations else 'none'} | target: {t2.operations[0].target_room if t2.operations else 'none'}")
pronoun_ok = t2.operations and t2.operations[0].target_room == "master_bedroom"
print(f"  -> Pronoun 'it' resolved to master_bedroom: {'PASS' if pronoun_ok else 'FAIL'}")

# -------------------------------------------------------------------------
# Test 4: Architect Engine Facade — feasibility check
# -------------------------------------------------------------------------
section("TEST 4: Architect Engine Facade — Infeasible Request Handling")

from aafpa.architect_engine_tools import ArchitectEngineFacade

facade = ArchitectEngineFacade()

# Try to expand master bedroom by 100 ft on a 32ft plot — should FAIL gracefully
result = facade.tool_resize_room(plan_a, room_type="master_bedroom", delta_ft=100.0, direction="increase")
print(f"Request: expand master bedroom by 100 ft on 32ft plot")
print(f"  -> Success: {result.success}")
print(f"  -> Message: {result.message[:140]}")
print(f"  -> Correct graceful failure: {'PASS' if not result.success else 'FAIL'}")

# Valid transfer
result2 = facade.tool_transfer_area(plan_a, source_type="corridor", dest_type="living_room", amount_sqft=20.0)
print(f"\nRequest: transfer 20 sqft from corridor to living room")
print(f"  -> Success: {result2.success}")
print(f"  -> Message: {result2.message[:140]}")

# -------------------------------------------------------------------------
# Test 5: Full Conversational Loop
# -------------------------------------------------------------------------
section("TEST 5: Full Conversational Studio Loop")

import os
if os.path.exists("session_state.pkl"):
    os.remove("session_state.pkl")

from aafpa.studio import InteractiveFloorPlanStudioSession

session = InteractiveFloorPlanStudioSession()

r1 = session.handle_message("I want a 2BHK on a 1000 sqft plot with modular kitchen, 2 bathrooms, balcony.")
print(f"Turn 1 (requirements):")
print(f"  status={r1['status']} | candidates={len(r1.get('candidates', []))}")

r2 = session.handle_message("2")
print(f"Turn 2 (select layout 2):")
print(f"  status={r2['status']} | selected={r2.get('selected_option')} | plan_version={getattr(r2.get('plan'), 'version', '?')}")

r3 = session.handle_message("Make the master bedroom bigger.")
print(f"Turn 3 (make master bedroom bigger):")
print(f"  status={r3['status']} | version={r3.get('version')}")
print(f"  explanation: {r3.get('explanation', '')[:100]}")

r4 = session.handle_message("Now make it wider instead of longer.")
print(f"Turn 4 (make it wider):")
print(f"  status={r4['status']} | version={r4.get('version')}")
print(f"  explanation: {r4.get('explanation', '')[:100]}")

r5 = session.handle_message("Make the house feel more spacious.")
print(f"Turn 5 (high-level goal: spacious):")
print(f"  status={r5['status']} | version={r5.get('version')}")
print(f"  explanation: {r5.get('explanation', '')[:120]}")

r6 = session.handle_message("undo")
print(f"Turn 6 (undo):")
print(f"  status={r6['status']}")
print(f"  explanation: {r6.get('explanation', '')[:100]}")

print(f"\n{'='*70}")
print("  SMOKE TEST COMPLETE")
print(f"{'='*70}")
