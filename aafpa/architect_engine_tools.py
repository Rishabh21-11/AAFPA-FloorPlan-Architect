"""
AAFPA 2.0 — Architect Engine Tool Facade
==========================================
Exposes the AAFPA Architect Engine's geometric and validation capabilities
as clean, strongly-typed tool functions callable by the Smart Agent.

Key design decisions:
- The Smart Agent NEVER writes Python geometry code directly.
- It calls these typed tool functions with structured payloads.
- Every tool validates its own preconditions before executing.
- Every tool returns a validated ToolResult with status, message,
  modified plan (if applicable), and a validation summary.
- This enforces the Two-Phase Commit Protocol:
    propose action -> validate feasibility -> execute or explain failure

Tools exposed:
    tool_get_plan_state      Get current plan as serializable dict
    tool_get_plan_condition  Get PlanConditionReport for the active plan
    tool_find_rooms          Find rooms by type, ID, or spatial relation
    tool_resize_room         Width, length, or area resize
    tool_transfer_area       Move area from source to target room
    tool_add_room            Add a new room with spatial placement
    tool_remove_room         Delete a room and redistribute its area
    tool_move_room           Relocate a room to a spatial position
    tool_replace_room        Replace one room type with another
    tool_swap_rooms          Swap positions of two rooms
    tool_improve_objective   High-level goal (spacious/privacy/ventilation)
    tool_validate_plan       Full constraint check on the active plan
    tool_render_plan         Render the plan and return matplotlib figure
    tool_undo                Undo to previous plan version
    tool_redo                Redo to next plan version
    tool_get_version_history Return list of version snapshots
"""

import copy
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

from aafpa.actions import ArchitecturalActionType, ArchitecturalOperation, DimensionSpec
from aafpa.geometry_engine import GenericGeometryEngine
from aafpa.spatial_reasoning import SpatialReasoningEngine
from aafpa.smart_agent import ConditionGroundedSmartAgent, PlanConditionReport


# ---------------------------------------------------------------------------
# Tool result schema
# ---------------------------------------------------------------------------
@dataclass
class ToolResult:
    """Standard return type for all Architect Engine tool calls."""
    success: bool
    message: str
    plan: Optional[Any] = None
    old_plan: Optional[Any] = None
    version: int = 0
    validation: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "version": self.version,
            "validation": self.validation,
            "warnings": self.warnings,
            "data": self.data,
        }


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------
def _quick_validate(plan: Any) -> Dict[str, Any]:
    """Runs lightweight constraint checks on a plan and returns a validation summary."""
    if plan is None:
        return {"hard_violations": 1, "overlap": False, "out_of_bounds": False,
                "nbc_min_area_ok": False, "notes": ["No plan provided."]}

    rooms = getattr(plan, "rooms", [])
    plot_w = getattr(getattr(plan, "plot", None), "width_ft", 32.0)
    plot_l = getattr(getattr(plan, "plot", None), "length_ft", 31.25)

    violations = []
    warnings = []
    overlap_detected = False
    out_of_bounds = False

    NBC_MIN_AREAS = {
        "master_bedroom": 100.0,
        "bedroom": 80.0,
        "living_room": 120.0,
        "kitchen": 50.0,
        "bathroom": 30.0,
        "dining": 70.0,
        "study": 60.0,
    }

    for r in rooms:
        w = getattr(r, "width", 0)
        l = getattr(r, "length", 0)
        x = getattr(r, "x", 0)
        y = getattr(r, "y", 0)
        area = w * l

        # Out of bounds check
        if x + w > plot_w + 0.5 or y + l > plot_l + 0.5:
            out_of_bounds = True
            violations.append(f"{r.id} extends beyond plot boundary")

        # Minimum dimension check (NBC 2016)
        min_area = NBC_MIN_AREAS.get(r.type, 0.0)
        if min_area > 0 and area < min_area * 0.7:   # 30% tolerance
            violations.append(f"{r.id} area {area:.0f} sqft below NBC minimum {min_area:.0f} sqft")

        if w < 3.0 or l < 3.0:
            violations.append(f"{r.id} dimension too small (w={w:.1f}, l={l:.1f})")

    # Overlap check (bounding box intersection)
    for i, r1 in enumerate(rooms):
        for r2 in rooms[i+1:]:
            r1x2, r1y2 = r1.x + r1.width, r1.y + r1.length
            r2x2, r2y2 = r2.x + r2.width, r2.y + r2.length
            if (r1.x < r2x2 - 0.3 and r1x2 > r2.x + 0.3 and
                    r1.y < r2y2 - 0.3 and r1y2 > r2.y + 0.3):
                overlap_detected = True
                warnings.append(f"Overlap detected between {r1.id} and {r2.id}")

    return {
        "hard_violations": len(violations),
        "violation_details": violations,
        "overlap": overlap_detected,
        "out_of_bounds": out_of_bounds,
        "nbc_ok": len(violations) == 0,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Architect Engine Facade
# ---------------------------------------------------------------------------
class ArchitectEngineFacade:
    """
    Tool facade exposing the AAFPA Architect Engine for use by the Smart Agent.
    All tools are stateless relative to the session; the caller (Studio/Agent) manages state.
    """

    def __init__(self):
        self.geometry_engine = GenericGeometryEngine()

    # -----------------------------------------------------------------------
    # Plan state tools
    # -----------------------------------------------------------------------
    def tool_get_plan_state(self, plan: Any) -> ToolResult:
        """Returns the current plan as a serializable summary dict."""
        if plan is None:
            return ToolResult(success=False, message="No active plan.")
        rooms = getattr(plan, "rooms", [])
        return ToolResult(
            success=True,
            message=f"Active plan v{getattr(plan, 'version', 1)} with {len(rooms)} rooms.",
            plan=plan,
            version=getattr(plan, "version", 1),
            data={
                "room_count": len(rooms),
                "rooms": [
                    {
                        "id": r.id,
                        "type": r.type,
                        "x": getattr(r, "x", 0),
                        "y": getattr(r, "y", 0),
                        "width": getattr(r, "width", 0),
                        "length": getattr(r, "length", 0),
                        "area": getattr(r, "area", 0),
                    }
                    for r in rooms
                ],
                "total_area": sum(getattr(r, "area", r.width * r.length) for r in rooms),
            },
        )

    def tool_get_plan_condition(self, plan: Any) -> ToolResult:
        """Diagnoses the current plan and returns a PlanConditionReport."""
        agent = ConditionGroundedSmartAgent()
        report = agent._diagnose_plan(plan)
        return ToolResult(
            success=True,
            message=report.to_summary(),
            plan=plan,
            data={
                "corridor_ratio": report.corridor_ratio,
                "has_excess_corridor": report.has_excess_corridor,
                "compartmentalized_public": report.compartmentalized_public,
                "poor_aspect_rooms": report.poor_aspect_rooms,
                "rooms_without_windows": report.rooms_without_windows,
                "bedrooms_near_entrance": report.bedrooms_near_entrance,
                "candidate_spaciousness_actions": report.candidate_spaciousness_actions,
                "candidate_privacy_actions": report.candidate_privacy_actions,
                "candidate_ventilation_actions": report.candidate_ventilation_actions,
            },
        )

    def tool_find_rooms(self, plan: Any, room_type: Optional[str] = None,
                         room_id: Optional[str] = None,
                         spatial_relation: Optional[str] = None,
                         anchor_room_id: Optional[str] = None) -> ToolResult:
        """Finds rooms matching given criteria."""
        if plan is None:
            return ToolResult(success=False, message="No active plan.")
        rooms = getattr(plan, "rooms", [])
        matched = []

        if room_id:
            matched = [r for r in rooms if r.id == room_id]
        elif room_type:
            matched = [r for r in rooms if r.type == room_type or room_type in r.type]
        elif spatial_relation:
            anchor = next((r for r in rooms if r.id == anchor_room_id), None) if anchor_room_id else None
            result = SpatialReasoningEngine.find_room_by_spatial_relation(
                rooms, spatial_relation, anchor_room=anchor
            )
            matched = [result] if result else []
        else:
            matched = rooms

        return ToolResult(
            success=bool(matched),
            message=f"Found {len(matched)} matching room(s).",
            data={"rooms": [{"id": r.id, "type": r.type, "area": getattr(r, "area", 0)} for r in matched]},
        )

    # -----------------------------------------------------------------------
    # Geometric modification tools
    # -----------------------------------------------------------------------
    def tool_resize_room(self, plan: Any, room_type: Optional[str] = None,
                          room_id: Optional[str] = None,
                          delta_ft: float = 2.0,
                          direction: str = "increase",
                          dimension: str = "auto") -> ToolResult:
        """
        Resizes a room by delta_ft in the specified dimension.
        dimension: "width" | "length" | "area" | "auto" (chooses shorter axis)
        direction: "increase" | "decrease"
        """
        if plan is None:
            return ToolResult(success=False, message="No active plan.")

        # Feasibility pre-check
        rooms = getattr(plan, "rooms", [])
        target = next((r for r in rooms if (room_id and r.id == room_id) or
                       (room_type and (r.type == room_type or room_type in r.type))), None)
        if not target:
            return ToolResult(success=False,
                              message=f"Room '{room_id or room_type}' not found in plan.")

        # Compute maximum feasible delta BEFORE executing
        plot_w = getattr(getattr(plan, "plot", None), "width_ft", 32.0)
        plot_l = getattr(getattr(plan, "plot", None), "length_ft", 31.25)
        max_delta_w = max(0.0, (plot_w - target.x) - target.width)
        max_delta_l = max(0.0, (plot_l - target.y) - target.length)
        max_feasible = max(max_delta_w, max_delta_l)

        if direction == "increase" and delta_ft > max_feasible + 0.5:
            return ToolResult(
                success=False,
                message=(
                    f"Cannot expand {target.type} by {delta_ft:.1f} ft — "
                    f"maximum feasible is {max_feasible:.1f} ft given plot boundaries. "
                    f"I can use {max_feasible:.1f} ft instead, or rearrange adjacent spaces."
                ),
                plan=plan,
                data={"max_feasible_delta": max_feasible},
            )

        # Map to action type
        if dimension == "width":
            action_type = ArchitecturalActionType.CHANGE_WIDTH
        elif dimension == "length":
            action_type = ArchitecturalActionType.CHANGE_LENGTH
        else:
            action_type = ArchitecturalActionType.RESIZE_ROOM

        op = ArchitecturalOperation(
            type=action_type,
            target_room=target.type,
            target_id=target.id,
            dimension=DimensionSpec(value=abs(delta_ft), unit="ft",
                                    direction=direction),
        )
        success, msg, new_plan = self.geometry_engine.apply_operations(plan, [op])
        validation = _quick_validate(new_plan)

        return ToolResult(
            success=success and validation["hard_violations"] == 0,
            message=msg,
            plan=new_plan,
            old_plan=plan,
            version=getattr(new_plan, "version", 1),
            validation=validation,
            warnings=validation.get("warnings", []),
        )

    def tool_transfer_area(self, plan: Any,
                            source_type: str, dest_type: str,
                            amount_sqft: float = 20.0,
                            source_id: Optional[str] = None,
                            dest_id: Optional[str] = None) -> ToolResult:
        """Transfers area from source room to destination room."""
        if plan is None:
            return ToolResult(success=False, message="No active plan.")

        rooms = getattr(plan, "rooms", [])
        src = next((r for r in rooms if (source_id and r.id == source_id) or
                    r.type == source_type), None)
        dst = next((r for r in rooms if (dest_id and r.id == dest_id) or
                    r.type == dest_type), None)

        if not src:
            return ToolResult(success=False, message=f"Source room '{source_type}' not found.")
        if not dst:
            return ToolResult(success=False, message=f"Destination room '{dest_type}' not found.")

        # Minimum area guard
        src_area = getattr(src, "area", src.width * src.length)
        NBC_MIN = {"master_bedroom": 100, "bedroom": 80, "living_room": 120,
                   "kitchen": 50, "bathroom": 30, "dining": 70}
        min_src = NBC_MIN.get(src.type, 40.0)
        max_transferable = max(0.0, src_area - min_src)

        if amount_sqft > max_transferable + 0.5:
            return ToolResult(
                success=False,
                message=(
                    f"Cannot transfer {amount_sqft:.0f} sqft from {src.type} — "
                    f"minimum area constraint requires keeping at least {min_src:.0f} sqft. "
                    f"Maximum transferable is {max_transferable:.0f} sqft."
                ),
                plan=plan,
                data={"max_transferable": max_transferable, "min_source_area": min_src},
            )

        op = ArchitecturalOperation(
            type=ArchitecturalActionType.TRANSFER_AREA,
            target_room=dst.type,
            target_id=dst.id,
            source_room=src.type,
            source_id=src.id,
            dimension=DimensionSpec(value=amount_sqft, unit="sqft"),
        )
        success, msg, new_plan = self.geometry_engine.apply_operations(plan, [op])
        validation = _quick_validate(new_plan)

        return ToolResult(
            success=success and validation["hard_violations"] == 0,
            message=msg, plan=new_plan, old_plan=plan,
            version=getattr(new_plan, "version", 1),
            validation=validation, warnings=validation.get("warnings", []),
        )

    def tool_add_room(self, plan: Any, room_type: str,
                       spatial_relation: Optional[str] = None,
                       relative_to_type: Optional[str] = None,
                       area_sqft: float = 80.0) -> ToolResult:
        """Adds a new room to the plan."""
        if plan is None:
            return ToolResult(success=False, message="No active plan.")

        anchor_id = None
        if relative_to_type:
            rooms = getattr(plan, "rooms", [])
            anchor = next((r for r in rooms if r.type == relative_to_type), None)
            if anchor:
                anchor_id = anchor.id

        op = ArchitecturalOperation(
            type=ArchitecturalActionType.ADD_ROOM,
            target_room=room_type,
            spatial_relation=spatial_relation,
            relative_target=relative_to_type,
            dimension=DimensionSpec(value=area_sqft, unit="sqft"),
        )
        success, msg, new_plan = self.geometry_engine.apply_operations(plan, [op])
        validation = _quick_validate(new_plan)

        return ToolResult(
            success=success, message=msg, plan=new_plan, old_plan=plan,
            version=getattr(new_plan, "version", 1),
            validation=validation, warnings=validation.get("warnings", []),
        )

    def tool_remove_room(self, plan: Any, room_type: Optional[str] = None,
                          room_id: Optional[str] = None) -> ToolResult:
        """Removes a room from the plan."""
        if plan is None:
            return ToolResult(success=False, message="No active plan.")

        rooms = getattr(plan, "rooms", [])
        target = next((r for r in rooms if (room_id and r.id == room_id) or
                       (room_type and r.type == room_type)), None)
        if not target:
            return ToolResult(success=False,
                              message=f"Room '{room_id or room_type}' not found.")

        op = ArchitecturalOperation(
            type=ArchitecturalActionType.REMOVE_ROOM,
            target_room=target.type,
            target_id=target.id,
        )
        success, msg, new_plan = self.geometry_engine.apply_operations(plan, [op])
        validation = _quick_validate(new_plan)

        return ToolResult(
            success=success, message=msg, plan=new_plan, old_plan=plan,
            version=getattr(new_plan, "version", 1),
            validation=validation, warnings=validation.get("warnings", []),
        )

    def tool_move_room(self, plan: Any, room_type: Optional[str] = None,
                        room_id: Optional[str] = None,
                        spatial_relation: Optional[str] = None,
                        relative_to_type: Optional[str] = None) -> ToolResult:
        """Moves a room to a new spatial position."""
        if plan is None:
            return ToolResult(success=False, message="No active plan.")

        op = ArchitecturalOperation(
            type=ArchitecturalActionType.MOVE_ROOM,
            target_room=room_type,
            target_id=room_id,
            spatial_relation=spatial_relation,
            relative_target=relative_to_type,
        )
        success, msg, new_plan = self.geometry_engine.apply_operations(plan, [op])
        validation = _quick_validate(new_plan)

        return ToolResult(
            success=success, message=msg, plan=new_plan, old_plan=plan,
            version=getattr(new_plan, "version", 1),
            validation=validation, warnings=validation.get("warnings", []),
        )

    def tool_replace_room(self, plan: Any, old_type: str, new_type: str) -> ToolResult:
        """Replaces one room type with another (same footprint)."""
        if plan is None:
            return ToolResult(success=False, message="No active plan.")

        op = ArchitecturalOperation(
            type=ArchitecturalActionType.REPLACE_ROOM,
            target_room=old_type,
            source_room=new_type,
        )
        success, msg, new_plan = self.geometry_engine.apply_operations(plan, [op])
        validation = _quick_validate(new_plan)

        return ToolResult(
            success=success, message=msg, plan=new_plan, old_plan=plan,
            version=getattr(new_plan, "version", 1),
            validation=validation, warnings=validation.get("warnings", []),
        )

    def tool_swap_rooms(self, plan: Any, type_a: str, type_b: str) -> ToolResult:
        """Swaps positions of two rooms."""
        if plan is None:
            return ToolResult(success=False, message="No active plan.")

        op = ArchitecturalOperation(
            type=ArchitecturalActionType.SWAP_ROOMS,
            target_room=type_a,
            source_room=type_b,
        )
        success, msg, new_plan = self.geometry_engine.apply_operations(plan, [op])
        validation = _quick_validate(new_plan)

        return ToolResult(
            success=success, message=msg, plan=new_plan, old_plan=plan,
            version=getattr(new_plan, "version", 1),
            validation=validation, warnings=validation.get("warnings", []),
        )

    def tool_improve_objective(self, plan: Any,
                                objective: str,
                                condition_report: Optional[Dict] = None) -> ToolResult:
        """
        Applies the best condition-grounded structural improvement for a high-level objective.
        objective: "spaciousness" | "privacy" | "ventilation" | "lighting" | "circulation"
        """
        if plan is None:
            return ToolResult(success=False, message="No active plan.")

        # Build the Smart Agent operation for this objective
        agent = ConditionGroundedSmartAgent()
        report = agent._diagnose_plan(plan)
        intent = agent._resolve_high_level_goal(objective, f"improve {objective}", plan, report)

        if not intent.operations:
            return ToolResult(success=True,
                              message=f"No structural change needed for '{objective}' given current plan state.",
                              plan=plan)

        success, msg, new_plan = self.geometry_engine.apply_operations(plan, intent.operations)
        validation = _quick_validate(new_plan)

        return ToolResult(
            success=success and validation["hard_violations"] == 0,
            message=msg, plan=new_plan, old_plan=plan,
            version=getattr(new_plan, "version", 1),
            validation=validation, warnings=validation.get("warnings", []),
            data={"diagnosis": report.to_summary(), "action_count": len(intent.operations)},
        )

    # -----------------------------------------------------------------------
    # Validation & rendering tools
    # -----------------------------------------------------------------------
    def tool_validate_plan(self, plan: Any) -> ToolResult:
        """Runs full constraint validation on the current plan."""
        validation = _quick_validate(plan)
        n_violations = validation.get("hard_violations", 0)
        status = "PASS" if n_violations == 0 else "FAIL"
        return ToolResult(
            success=n_violations == 0,
            message=f"Validation {status}: {n_violations} hard violation(s).",
            plan=plan,
            validation=validation,
            warnings=validation.get("warnings", []),
        )

    def tool_render_plan(self, plan: Any, title: str = "Active Floor Plan",
                          version: int = 1, save_path: str = "active_floor_plan.png") -> ToolResult:
        """Renders the plan using matplotlib and saves to disk. Returns figure object."""
        if plan is None:
            return ToolResult(success=False, message="No active plan to render.")

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            rooms = getattr(plan, "rooms", [])
            plot_w = getattr(getattr(plan, "plot", None), "width_ft", 32.0)
            plot_l = getattr(getattr(plan, "plot", None), "length_ft", 31.25)

            ROOM_COLORS = {
                "living_room": "#E0E7FF", "master_bedroom": "#E2E8F0",
                "bedroom": "#F1F5F9", "kitchen": "#FEF08A", "dining": "#FEF3C7",
                "bathroom": "#BAE6FD", "balcony": "#D1FAE5", "study": "#EDE9FE",
                "pooja_room": "#FFEDD5", "corridor": "#F8FAFC", "foyer": "#FDF4FF",
                "utility": "#ECFDF5", "default": "#F1F5F9",
            }

            fig, ax = plt.subplots(1, 1, figsize=(10, 8.5), dpi=120)
            ax.set_xlim(-2, plot_w + 2)
            ax.set_ylim(-2, plot_l + 2)
            ax.set_aspect("equal")
            ax.invert_yaxis()
            ax.set_facecolor("#FCFCFD")
            fig.patch.set_facecolor("#F0F4F8")

            # Plot outer boundary
            ax.add_patch(plt.Rectangle(
                (0, 0), plot_w, plot_l,
                fill=True, facecolor="#FFFFFF", edgecolor="#0F172A",
                linewidth=2.5, zorder=2
            ))

            for r in rooms:
                c = ROOM_COLORS.get(r.type, ROOM_COLORS["default"])
                ax.add_patch(plt.Rectangle(
                    (r.x, r.y), r.width, r.length,
                    facecolor=c, edgecolor="#475569", linewidth=1.5, zorder=3
                ))
                cx, cy = r.x + r.width / 2.0, r.y + r.length / 2.0
                label = r.type.replace("_", " ").title()
                ax.text(cx, cy - 0.35, label, ha="center", va="center",
                        fontsize=8.5, fontweight="bold", color="#0F172A", zorder=7)
                dim_txt = f"{r.width:.1f}' x {r.length:.1f}'\n({getattr(r, 'area', r.width * r.length):.0f} sqft)"
                ax.text(cx, cy + 0.6, dim_txt, ha="center", va="center",
                        fontsize=6.5, color="#334155", zorder=7)

            total_area = sum(getattr(r, "area", r.width * r.length) for r in rooms)
            ax.set_title(
                f"AAFPA 2.0  {title} (v{version})\n"
                f"Plot: {plot_w:.0f}' x {plot_l:.0f}'  |  Built-up: {total_area:.0f} sqft  |  Rooms: {len(rooms)}",
                fontsize=10, fontweight="bold", color="#0F172A", pad=10
            )
            ax.axis("off")
            plt.tight_layout()
            plt.savefig(save_path, dpi=130, bbox_inches="tight")

            return ToolResult(
                success=True,
                message=f"Rendered to '{save_path}'.",
                plan=plan,
                data={"figure": fig, "save_path": save_path},
            )
        except Exception as e:
            return ToolResult(success=False, message=f"Render failed: {e}", plan=plan)

    # -----------------------------------------------------------------------
    # Version control tools
    # -----------------------------------------------------------------------
    def tool_undo(self, memory: Any) -> ToolResult:
        """Reverts to the previous plan version."""
        restored = memory.undo()
        if restored:
            return ToolResult(
                success=True,
                message=f"Reverted to plan version {getattr(restored, 'version', '?')}.",
                plan=restored,
                version=getattr(restored, "version", 0),
            )
        return ToolResult(success=False, message="No previous version available to undo.")

    def tool_redo(self, memory: Any) -> ToolResult:
        """Re-applies a previously undone plan version."""
        restored = memory.redo()
        if restored:
            return ToolResult(
                success=True,
                message=f"Re-applied plan version {getattr(restored, 'version', '?')}.",
                plan=restored,
                version=getattr(restored, "version", 0),
            )
        return ToolResult(success=False, message="Nothing to redo.")

    def tool_get_version_history(self, memory: Any) -> ToolResult:
        """Returns the list of saved plan versions."""
        history = getattr(memory, "history", [])
        return ToolResult(
            success=True,
            message=f"{len(history)} version(s) in history.",
            data={
                "versions": [
                    {
                        "index": i,
                        "version": h.get("version", i),
                        "description": h.get("description", ""),
                    }
                    for i, h in enumerate(history)
                ]
            },
        )
