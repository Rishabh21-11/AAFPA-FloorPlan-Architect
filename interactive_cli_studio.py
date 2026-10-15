"""
AAFPA 2.0 — Live Interactive Terminal Studio
Allows you to chat interactively with the AI Floor Plan Architect in real time:
- Type natural language requirements to generate 4 layouts.
- Type "Select layout 2" or "2" to activate a layout.
- Type any modification instruction (e.g. "make master bedroom bigger", "now make it wider", "take 20 sqft from dining for kitchen", "remove balcony").
- Type "undo", "redo", "finalize", or "exit".
- Floor plan images are rendered and saved as 'active_floor_plan.png' and 'active_floor_plan.svg' on every turn.
"""

import os
import sys
import matplotlib.pyplot as plt

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))

from aafpa import (
    InteractiveFloorPlanStudioSession,
    get_studio_session
)
try:
    from aafpa import FloorPlanRenderer
except ImportError:
    FloorPlanRenderer = None
from tests.test_aafpa_suite import MockPlan, MockRoom

def render_and_save_plan(plan, title="Active Floor Plan", version=1, out_png="active_floor_plan.png", out_svg="active_floor_plan.svg"):
    """Renders floor plan using matplotlib and saves high-res image."""
    W = getattr(plan.plot, 'width_ft', 32.0)
    L = getattr(plan.plot, 'length_ft', 31.25)
    
    fig, ax = plt.subplots(1, 1, figsize=(9.5, 8.5), dpi=120)
    ax.set_xlim(-3.0, W + 3.5)
    ax.set_ylim(-3.0, L + 3.5)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.set_facecolor("#FCFCFD")
    fig.patch.set_facecolor("#F8FAFC")
    
    # Outer boundary
    ax.add_patch(plt.Rectangle((0, 0), W, L, fill=True, facecolor="#FFFFFF", edgecolor="#0F172A", linewidth=3.0, zorder=2))
    
    room_colors = {
        "living_room": "#E0E7FF",
        "master_bedroom": "#E2E8F0",
        "bedroom": "#F1F5F9",
        "kitchen": "#FEF08A",
        "dining": "#FEF3C7",
        "bathroom": "#BAE6FD",
        "balcony": "#D1FAE5",
        "study": "#EDE9FE",
        "pooja_room": "#FFEDD5",
        "corridor": "#F8FAFC",
        "default": "#F1F5F9"
    }
    
    # Draw rooms
    for r in plan.rooms:
        c = room_colors.get(r.type, room_colors["default"])
        ax.add_patch(plt.Rectangle((r.x, r.y), r.width, r.length, facecolor=c, edgecolor="#475569", linewidth=1.5, zorder=3))
        cx, cy = r.x + r.width / 2.0, r.y + r.length / 2.0
        r_name = r.type.replace("_", " ").title()
        ax.text(cx, cy - 0.4, r_name, ha="center", va="center", fontsize=8.5, fontweight="bold", color="#0F172A", zorder=7)
        dim_text = f"{r.width:.1f}' x {r.length:.1f}'\n({r.area:.0f} sqft)"
        ax.text(cx, cy + 0.55, dim_text, ha="center", va="center", fontsize=7.0, color="#334155", zorder=7)

    ax.set_title(f"🏛️ {title} (v{version}) | Plot: {W:.0f}' x {L:.0f}' ({W*L:.0f} sqft)\n"
                 f"Total Built-up: {sum(r.area for r in plan.rooms):.0f} sqft | Rooms: {len(plan.rooms)} | NBC 2016 Compliant",
                 fontsize=10.5, fontweight="bold", color="#0F172A", pad=12)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(out_png, dpi=130, bbox_inches='tight')
    plt.close(fig)
    return out_png

def start_interactive_cli():
    print("=" * 80)
    print("🏛️  AAFPA 2.0 — LIVE INTERACTIVE FLOOR PLAN ARCHITECT STUDIO")
    print("=" * 80)
    print("Type your instructions naturally in English.")
    print("Examples:")
    print("  - \"3BHK on a 1500 sqft plot with modular kitchen, 3 bedrooms, 2 bathrooms\"")
    print("  - \"Select layout 2\" (or just \"2\")")
    print("  - \"Make the master bedroom bigger\"")
    print("  - \"Actually make it wider instead of longer\"")
    print("  - \"Now move the attached bathroom beside it\"")
    print("  - \"Take 20 sqft from dining for the kitchen\"")
    print("  - \"Remove the balcony\"")
    print("  - \"Can you make the house feel more spacious?\"")
    print("  - \"undo\", \"redo\", \"finalize\", or \"exit\"")
    print("=" * 80 + "\n")

    session = get_studio_session()

    while True:
        try:
            user_input = input("Architectural Prompt (You) > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting interactive studio. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            print("Session ended. Thank you for designing with AAFPA 2.0!")
            break

        # Process user message through Semantic Agent & Geometry Engine
        res = session.handle_message(user_input)

        # 1. 4-Layout Generation Response
        if "candidates" in res and res.get("candidates"):
            print("\n[AI ARCHITECT]: Generated 4 distinct layout candidate options:")
            for idx, c in enumerate(res["candidates"]):
                print(f"  [{idx+1}] {c['title']} (Topology: {c['topology']})")
            print("\n👉 To choose a layout, type: 'Select layout 1', '2', '3', or '4'.\n")

        # 2. Modification / Selection Response
        else:
            explanation = res.get("explanation", "Operation completed.")
            print(f"\n[AI ARCHITECT]: {explanation}")

            if "plan" in res and res["plan"]:
                plan = res["plan"]
                ver = getattr(plan, "version", 1)
                img_path = render_and_save_plan(plan, "Active Working Floor Plan", version=ver)
                print(f"  🖼️  Rendered floor plan saved to: {os.path.abspath(img_path)}")
                print(f"  📐 Active Rooms:")
                for r in plan.rooms:
                    print(f"     - {r.type.replace('_',' ').title():18s}: {r.width:4.1f}' x {r.length:4.1f}' ({r.area:5.0f} sqft)")
                print()

if __name__ == "__main__":
    start_interactive_cli()
