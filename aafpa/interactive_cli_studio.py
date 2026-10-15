"""
AAFPA 2.0 — Persistent Interactive Prompt Console
===================================================
Section 24B — Live Interactive Architectural Chat

Run this cell in Jupyter to start an interactive, persistent conversational
session with the AAFPA Smart Architectural Agent.

Features:
  - Full condition-grounded reasoning (plan state inspected before every response)
  - Discourse entity tracking (pronouns and "that room" resolve correctly)
  - Two-Phase Commit: impossible requests are explained, not hallucinated
  - Automatic floor plan rendering after every successful edit
  - Undo / redo / finalize via natural language
  - Type 'exit', 'quit', or 'done' to end the session

Usage:
  From Jupyter: run this cell → type in the prompt box
  From CLI: python aafpa/interactive_cli_studio.py
"""

import os
import sys

# ---- Ensure AAFPA is importable ----
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from aafpa.studio import InteractiveFloorPlanStudioSession, get_studio_session


# ---- Session banner ----
BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║   AAFPA 2.0  ─  AI Agentic Floor Plan Architect  ─  Smart Studio Console    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Powered by Condition-Grounded Reasoning + HouseMind Dataset                ║
║  Commands: describe a house ─ select layout ─ make edits ─ undo ─ finalize  ║
║  Type 'exit' or 'quit' to end the session.                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


def _display_response(response: dict, show_figures: bool = True) -> None:
    """Pretty-prints an AAFPA studio response."""
    status = response.get("status", "unknown")
    explanation = response.get("explanation", "")
    plan = response.get("plan")
    version = response.get("version")
    validation = response.get("validation", {})
    candidates = response.get("candidates", [])

    # Status line
    status_icon = {
        "success": "✓",
        "partial": "⚠",
        "finalized": "🔒",
        "error": "✗",
        "warning": "⚠",
        "constraint_violation": "⛔",
        "validation_failed": "⛔",
        "clarification": "❓",
        "waiting_requirements": "💬",
        "layout_selection": "🏗",
    }.get(status, "→")

    print(f"\n{status_icon}  [{status.upper()}]  {explanation}")

    # Show layout options
    if candidates:
        print(f"\n  📐  Generated {len(candidates)} layout options:")
        for c in candidates:
            print(f"      {c.get('label', '?')}: {c.get('title', '?')}")
            desc = c.get("description", "")
            if desc:
                print(f"           {desc[:90]}")
        print("\n  → Reply with a number (1–4) to select a layout.")

    # Plan info
    if plan and not candidates:
        rooms = getattr(plan, "rooms", [])
        total_area = sum(getattr(r, "area", r.width * r.length) for r in rooms)
        ver_str = f"v{version}" if version else f"v{getattr(plan, 'version', '?')}"
        print(f"\n  📋  Plan {ver_str} | {len(rooms)} rooms | {total_area:.0f} sqft")
        for r in rooms:
            area_val = getattr(r, "area", r.width * r.length)
            print(f"      {r.type.replace('_',' ').title():<22} {r.width:.1f}' x {r.length:.1f}' = {area_val:.0f} sqft")

    # Validation warnings
    if validation.get("warnings"):
        for w in validation["warnings"]:
            print(f"  ⚠  {w}")
    if validation.get("violation_details"):
        for v in validation["violation_details"]:
            print(f"  ⛔  {v}")

    # Figure
    fig = response.get("figure")
    if fig and show_figures:
        try:
            import matplotlib
            # If we're in Jupyter, just call plt.show()
            try:
                from IPython.display import display as ipy_display
                ipy_display(fig)
            except ImportError:
                fig.savefig("aafpa_current_plan.png", dpi=120, bbox_inches="tight")
                print(f"  🖼  Floor plan saved → aafpa_current_plan.png")
            plt.close(fig)
        except Exception as e:
            pass
    elif plan and not candidates:
        # Render and save
        try:
            from aafpa.architect_engine_tools import ArchitectEngineFacade
            facade = ArchitectEngineFacade()
            ver = version or getattr(plan, "version", 1)
            r = facade.tool_render_plan(plan, title="Active Floor Plan", version=ver,
                                         save_path="aafpa_current_plan.png")
            print(f"  🖼  Floor plan saved → aafpa_current_plan.png")
            if r.data.get("figure"):
                try:
                    from IPython.display import display as ipy_display
                    ipy_display(r.data["figure"])
                except ImportError:
                    pass
                plt.close(r.data["figure"])
        except Exception:
            pass


def run_interactive_console(orchestrator=None, show_figures: bool = True) -> None:
    """
    Starts a persistent interactive AAFPA architectural conversation.
    Works in both Jupyter notebooks (inline plots) and CLI mode.
    """
    print(BANNER)

    # Create a fresh session (or resume if state file exists)
    session = get_studio_session(orchestrator)
    if session.current_state == "initial":
        print("  💬  Please describe the house you want to design.\n")
        print("  Example: 'I want a 2BHK house on a 30x40 ft plot with modular kitchen,")
        print("            2 bathrooms, a balcony, and Vastu compliance.'\n")

    try:
        while True:
            try:
                user_input = input("  You ▶  ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n  Goodbye! Your session has been saved.")
                break

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "done", "bye"):
                print("\n  Session ended. Your floor plan session state has been saved.")
                print("  Run the console again to continue where you left off.")
                break

            if user_input.lower() in ("reset", "restart", "new session"):
                session.reset()
                print("  ✓  Session reset. Describe a new house to begin.")
                continue

            if user_input.lower() in ("help", "?", "commands"):
                print("""
  Available commands:
    Describe a house     → "I want a 3BHK on a 1200 sqft plot..."
    Select a layout      → "Select layout 2" or just "2"
    Resize a room        → "Make the master bedroom bigger by 20 sqft"
    Transfer area        → "Take 15 sqft from the corridor and give it to the kitchen"
    Add a room           → "Add a study room beside the master bedroom"
    Remove a room        → "Remove the utility room"
    Move a room          → "Move the kitchen to the back"
    Swap rooms           → "Swap the bedroom and the study"
    High-level goals     → "Make the house more spacious" / "Improve ventilation"
    Vastu               → "Apply Vastu guidelines"
    Undo / Redo          → "undo" / "redo"
    Finalize             → "finalize the plan"
    Reset session        → "reset" or "new session"
    Exit                 → "exit" or "quit"
""")
                continue

            if user_input.lower() in ("status", "plan", "current plan"):
                plan = session.memory.current_plan
                if plan:
                    rooms = getattr(plan, "rooms", [])
                    total = sum(getattr(r, "area", r.width * r.length) for r in rooms)
                    ver = getattr(plan, "version", 1)
                    print(f"\n  📋  Current Plan v{ver} | {len(rooms)} rooms | {total:.0f} sqft")
                    for r in rooms:
                        area_val = getattr(r, "area", r.width * r.length)
                        print(f"      {r.type.replace('_', ' ').title():<22} {area_val:.0f} sqft")
                else:
                    print("  No active plan. Please describe a house to get started.")
                continue

            # Process through AAFPA Smart Agent
            print("  Agent ◀  Analysing...", end="", flush=True)
            try:
                response = session.handle_message(user_input)
                print("\r" + " " * 30 + "\r", end="")  # Clear "Analysing..."
                _display_response(response, show_figures=show_figures)
            except Exception as e:
                print(f"\n  ✗  Error: {e}")
                import traceback
                traceback.print_exc()

    finally:
        session._save_state()


# ---- Jupyter-friendly entry point ----
def start_console_in_notebook(orchestrator=None):
    """
    Convenience wrapper for running inside a Jupyter cell.
    Usage in Jupyter:
        from aafpa.interactive_cli_studio import start_console_in_notebook
        start_console_in_notebook()
    """
    run_interactive_console(orchestrator=orchestrator, show_figures=True)


# ---- CLI entry point ----
if __name__ == "__main__":
    run_interactive_console(show_figures=False)
