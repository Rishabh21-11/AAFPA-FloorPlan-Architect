"""
AAFPA 2.0 End-to-End Architectural Assistant Demonstration Walkthrough
Demonstrates the full conversational intelligence lifecycle:
Initial Request -> 4 Layout Generation -> Selection -> Multi-Turn Natural Language Edits -> Area Transfer -> Spatial Reasoning -> Undo -> Final Rendering.
"""

import os
import sys
import matplotlib.pyplot as plt
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))

from aafpa import (
    InteractiveFloorPlanStudioSession,
    get_studio_session,
    aafpa_chat,
    aafpa_select_layout,
    aafpa_finalize,
    aafpa_edit,
    EvaluationBenchmark
)

def run_demo():
    print("=" * 80)
    print("🏛️  AAFPA 2.0 — AI AGENTIC FLOOR PLAN ARCHITECT (END-TO-END DEMO)")
    print("=" * 80)

    # Initialize studio session
    session = get_studio_session()

    # Step 1: Initial natural-language prompt
    prompt_1 = "3BHK on a 1500 sqft plot with a large living room, modular kitchen, 3 bedrooms and 2 bathrooms."
    print(f"\n[USER TURN 1]: \"{prompt_1}\"")
    res1 = session.handle_message(prompt_1)
    print(f"[SYSTEM]: Generated 4 distinct layout candidate options:")
    for idx, c in enumerate(res1.get("candidates", [])):
        print(f"  - Option {idx+1}: {c['title']} (Topology: {c['topology']})")

    # Step 2: User selects layout 2
    prompt_2 = "Select layout 2."
    print(f"\n[USER TURN 2]: \"{prompt_2}\"")
    res2 = session.handle_message(prompt_2)
    print(f"[SYSTEM]: {res2['explanation']}")

    # Step 3: Resize master bedroom
    prompt_3 = "Make the master bedroom bigger."
    print(f"\n[USER TURN 3]: \"{prompt_3}\"")
    res3 = session.handle_message(prompt_3)
    print(f"[SYSTEM]: {res3['explanation']}")
    print(f"  Structured Action IR: {res3['structured_intent']['operations'][0]}")

    # Step 4: Multi-turn pronoun resolution & width change
    prompt_4 = "Actually, make it wider instead of longer."
    print(f"\n[USER TURN 4]: \"{prompt_4}\"")
    res4 = session.handle_message(prompt_4)
    print(f"[SYSTEM]: {res4['explanation']}")
    print(f"  Structured Action IR: {res4['structured_intent']['operations'][0]}")

    # Step 5: Relative spatial move
    prompt_5 = "Now move the attached bathroom beside it."
    print(f"\n[USER TURN 5]: \"{prompt_5}\"")
    res5 = session.handle_message(prompt_5)
    print(f"[SYSTEM]: {res5['explanation']}")

    # Step 6: Area transfer
    prompt_6 = "Make the bathroom slightly smaller and use the extra space for the bedroom."
    print(f"\n[USER TURN 6]: \"{prompt_6}\"")
    res6 = session.handle_message(prompt_6)
    print(f"[SYSTEM]: {res6['explanation']}")

    # Step 7: Room removal
    prompt_7 = "Remove the balcony."
    print(f"\n[USER TURN 7]: \"{prompt_7}\"")
    res7 = session.handle_message(prompt_7)
    print(f"[SYSTEM]: {res7['explanation']}")

    # Step 8: High-level design objective
    prompt_8 = "Can you make the house feel more spacious?"
    print(f"\n[USER TURN 8]: \"{prompt_8}\"")
    res8 = session.handle_message(prompt_8)
    print(f"[SYSTEM]: {res8['explanation']}")

    # Step 9: Undo operation
    prompt_9 = "Undo that."
    print(f"\n[USER TURN 9]: \"{prompt_9}\"")
    res9 = session.handle_message(prompt_9)
    print(f"[SYSTEM]: {res9['explanation']}")

    # Step 10: Finalize plan
    prompt_10 = "Finalize plan."
    print(f"\n[USER TURN 10]: \"{prompt_10}\"")
    res10 = session.handle_message(prompt_10)
    print(f"[SYSTEM]: {res10['explanation']}")

    # Run Benchmark
    print("\n" + "=" * 80)
    print("📊 RUNNING 13-METRIC EVALUATION BENCHMARK SUITE")
    print("=" * 80)
    benchmark = EvaluationBenchmark(session.semantic_agent)
    metrics = benchmark.run_full_benchmark(num_samples=50)
    for k, v in metrics.items():
        print(f"  {k:55s}: {v}")

    print("\n🎉 ALL AAFPA 2.0 DEMO STEPS & EVALUATION COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run_demo()
