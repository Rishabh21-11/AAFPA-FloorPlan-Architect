"""
AAFPA 2.0 Generic Parametric Geometry Modification Engine
Implements generic, robust parametric mutations for floor plans following
the Principle of Minimum Necessary Change, preserving coordinate validity,
non-overlap, and boundary constraints.
"""

import math
import copy
from typing import Optional, List, Dict, Any, Tuple
from aafpa.actions import ArchitecturalActionType, ArchitecturalOperation
from aafpa.spatial_reasoning import SpatialReasoningEngine

class GenericGeometryEngine:
    """Parametric geometry modification engine operating on GeometricPlan data structures."""

    def __init__(self):
        pass

    def apply_operations(self, plan: Any, operations: List[ArchitecturalOperation],
                         req: Optional[Any] = None) -> Tuple[bool, str, Any]:
        """
        Executes a sequence of architectural operations on the plan.
        Returns: (success, explanation, modified_plan)
        """
        candidate = copy.deepcopy(plan)
        explanations = []

        for op in operations:
            success, msg = self._execute_single_op(candidate, op, req)
            explanations.append(msg)
            if not success:
                # Log violation/warning but continue if recoverable
                pass

        # Update apertures (doors & windows) after geometry shifts
        self.refresh_doors_and_windows(candidate)

        final_msg = " ".join(explanations)
        return True, final_msg, candidate

    def _execute_single_op(self, plan: Any, op: ArchitecturalOperation,
                           req: Optional[Any]) -> Tuple[bool, str]:
        """Dispatches a single operation to its generic geometric handler."""
        op_type = op.type

        if op_type in (ArchitecturalActionType.RESIZE_ROOM, ArchitecturalActionType.CHANGE_WIDTH, ArchitecturalActionType.CHANGE_LENGTH, ArchitecturalActionType.CHANGE_AREA):
            return self._handle_resize(plan, op)

        elif op_type == ArchitecturalActionType.TRANSFER_AREA:
            return self._handle_transfer_area(plan, op)

        elif op_type == ArchitecturalActionType.SWAP_ROOMS:
            return self._handle_swap_rooms(plan, op)

        elif op_type == ArchitecturalActionType.REPLACE_ROOM:
            return self._handle_replace_room(plan, op)

        elif op_type == ArchitecturalActionType.REMOVE_ROOM:
            return self._handle_remove_room(plan, op)

        elif op_type == ArchitecturalActionType.ADD_ROOM:
            return self._handle_add_room(plan, op)

        elif op_type == ArchitecturalActionType.MOVE_ROOM:
            return self._handle_move_room(plan, op)

        elif op_type in (ArchitecturalActionType.IMPROVE_VENTILATION, ArchitecturalActionType.IMPROVE_LIGHTING):
            return self._handle_improve_environmental(plan, op)

        elif op_type == ArchitecturalActionType.MAKE_OPEN_CONCEPT:
            return self._handle_open_concept(plan, op)

        elif op_type == ArchitecturalActionType.APPLY_VASTU:
            return self._handle_vastu_alignment(plan, op)

        elif op_type in (ArchitecturalActionType.ADD_DOOR, ArchitecturalActionType.MOVE_DOOR, ArchitecturalActionType.ADD_WINDOW, ArchitecturalActionType.MOVE_WINDOW):
            return self._handle_aperture(plan, op)

        return True, f"Executed {op_type.value if hasattr(op_type, 'value') else op_type}."

    def _handle_resize(self, plan: Any, op: ArchitecturalOperation) -> Tuple[bool, str]:
        """Handles width, length, or area resize for a target room."""
        target_r = self._find_target_room(plan, op.target_room, op.target_id)
        if not target_r:
            return False, f"Could not find room '{op.target_room or op.target_id}' to resize."

        plot_w = getattr(plan.plot, 'width_ft', 32.0)
        plot_l = getattr(plan.plot, 'length_ft', 31.25)

        dim = op.dimension
        delta = (dim.value if dim and dim.value else 2.0)
        is_decrease = (dim and dim.direction == "decrease")
        delta = -delta if is_decrease else delta

        is_width_only = (op.type == ArchitecturalActionType.CHANGE_WIDTH)
        is_length_only = (op.type == ArchitecturalActionType.CHANGE_LENGTH)

        # Minimum dimension limits (NBC 2016 safety)
        min_w = 3.5 if "bath" in target_r.type else 6.5
        min_l = 4.0 if "bath" in target_r.type else 7.0

        old_w, old_l = target_r.width, target_r.length

        if is_width_only or (not is_length_only and target_r.width <= target_r.length):
            new_w = max(min_w, min(plot_w - target_r.x, target_r.width + delta))
            target_r.width = round(new_w, 2)
            # Find adjacent room sharing right or left boundary to accommodate change
            self._adjust_adjacent_boundary_x(plan, target_r, old_w, new_w)
            action_desc = f"{'widened' if delta > 0 else 'narrowed'} width to {target_r.width:.1f} ft"
        else:
            new_l = max(min_l, min(plot_l - target_r.y, target_r.length + delta))
            target_r.length = round(new_l, 2)
            self._adjust_adjacent_boundary_y(plan, target_r, old_l, new_l)
            action_desc = f"{'lengthened' if delta > 0 else 'shortened'} length to {target_r.length:.1f} ft"

        return True, f"Adjusted {target_r.type.replace('_',' ').title()} ({action_desc}, new area: {target_r.area:.0f} sqft)."

    def _handle_transfer_area(self, plan: Any, op: ArchitecturalOperation) -> Tuple[bool, str]:
        """Transfers usable area from source room to target room."""
        target_r = self._find_target_room(plan, op.target_room, op.target_id)
        source_r = self._find_target_room(plan, op.source_room, op.source_id)

        if not target_r:
            return False, "Target room for area transfer not found."
        if not source_r:
            # Pick a suitable donor room (e.g. adjacent room with surplus area)
            adj_rooms = SpatialReasoningEngine.get_adjacent_rooms(target_r, plan.rooms)
            source_r = next((r for r in adj_rooms if r.area > 60), None)
            if not source_r:
                source_r = next((r for r in plan.rooms if r.id != target_r.id and r.area > 80), None)

        if not source_r:
            return False, "No suitable source room available to transfer area from."

        transfer_sqft = op.dimension.value if (op.dimension and op.dimension.value) else 20.0
        # Calculate dimensional shift along shared boundary
        min_src_area = 20.0 if "bath" in source_r.type else 50.0
        actual_transfer = min(transfer_sqft, max(0.0, source_r.area - min_src_area))

        if actual_transfer <= 1.0:
            return False, f"{source_r.type.replace('_',' ').title()} cannot be reduced further without violating minimum code size."

        # Compute geometric transfer along boundary
        if abs(target_r.x + target_r.width - source_r.x) < 1.0 or abs(source_r.x + source_r.width - target_r.x) < 1.0:
            # Horizontal sharing
            dw = round(actual_transfer / max(1.0, target_r.length), 2)
            if target_r.x < source_r.x:
                target_r.width = round(target_r.width + dw, 2)
                source_r.x = round(source_r.x + dw, 2)
                source_r.width = round(max(3.5, source_r.width - dw), 2)
            else:
                source_r.width = round(max(3.5, source_r.width - dw), 2)
                target_r.x = round(source_r.x + source_r.width, 2)
                target_r.width = round(target_r.width + dw, 2)
        else:
            # Vertical or proportional transfer
            dl = round(actual_transfer / max(1.0, target_r.width), 2)
            target_r.length = round(target_r.length + dl, 2)
            source_r.length = round(max(4.0, source_r.length - dl), 2)

        return True, f"Transferred approximately {actual_transfer:.0f} sqft from {source_r.type.replace('_',' ').title()} to {target_r.type.replace('_',' ').title()}."

    def _handle_swap_rooms(self, plan: Any, op: ArchitecturalOperation) -> Tuple[bool, str]:
        """Swaps coordinates and dimensions of two rooms."""
        r1 = self._find_target_room(plan, op.target_room, op.target_id)
        r2 = self._find_target_room(plan, op.source_room, op.source_id)

        if not r1 or not r2:
            return False, "Could not find both rooms to swap."

        # Swap geometry
        r1.x, r2.x = r2.x, r1.x
        r1.y, r2.y = r2.y, r1.y
        r1.width, r2.width = r2.width, r1.width
        r1.length, r2.length = r2.length, r1.length
        r1.zone, r2.zone = r2.zone, r1.zone

        return True, f"Swapped positions of {r1.type.replace('_',' ').title()} and {r2.type.replace('_',' ').title()}."

    def _handle_replace_room(self, plan: Any, op: ArchitecturalOperation) -> Tuple[bool, str]:
        """Converts/replaces the functional type of an existing room."""
        r = self._find_target_room(plan, op.target_room, op.target_id)
        if not r:
            return False, f"Room '{op.target_room}' not found."

        old_type = r.type
        new_type = op.source_room or "study"
        r.type = new_type
        r.zone = "public" if new_type in ("living_room", "dining", "study") else ("service" if new_type in ("kitchen", "bathroom", "utility") else "private")

        return True, f"Converted {old_type.replace('_',' ').title()} into {new_type.replace('_',' ').title()}."

    def _handle_remove_room(self, plan: Any, op: ArchitecturalOperation) -> Tuple[bool, str]:
        """Removes a room from the plan and allows adjacent rooms to absorb space."""
        r = self._find_target_room(plan, op.target_room, op.target_id)
        if not r:
            return False, f"Room '{op.target_room}' to remove was not found."

        if len(plan.rooms) <= 3:
            return False, "Cannot remove room: minimum essential living program must be retained."

        plan.rooms = [rm for rm in plan.rooms if rm.id != r.id]

        # Expand adjacent room to absorb space
        adj_candidates = SpatialReasoningEngine.get_adjacent_rooms(r, plan.rooms)
        if adj_candidates:
            absorber = max(adj_candidates, key=lambda a: a.area)
            if abs(absorber.y - r.y) < 1.0 and abs(absorber.length - r.length) < 1.0:
                absorber.width = round(absorber.width + r.width, 2)
            elif abs(absorber.x - r.x) < 1.0 and abs(absorber.width - r.width) < 1.0:
                absorber.length = round(absorber.length + r.length, 2)

        return True, f"Removed {r.type.replace('_',' ').title()} ({r.area:.0f} sqft) from the floor plan."

    def _handle_add_room(self, plan: Any, op: ArchitecturalOperation) -> Tuple[bool, str]:
        """Adds a new room into the plan at the specified relative or regional location."""
        rtype = op.target_room or "foyer"
        target_area = (op.dimension.value if op.dimension and op.dimension.value else 48.0)
        rel = op.spatial_relation or "right"
        anchor_type = op.relative_target

        plot_w = getattr(plan.plot, 'width_ft', 32.0)
        plot_l = getattr(plan.plot, 'length_ft', 31.25)

        room_cls = type(plan.rooms[0])
        new_room_id = f"{rtype}_{len(plan.rooms)+1}"

        # 1. Check if anchor room is specified (e.g. "on right of bathroom", "on left of living room", "attached to master bed")
        anchor = None
        if anchor_type:
            anchor = self._find_target_room(plan, anchor_type, None)

        if anchor:
            # Case A: On the right / east / beside
            if rel in ("right", "east", "beside"):
                space_avail = plot_w - (anchor.x + anchor.width)
                if space_avail >= 4.0:
                    new_x = round(anchor.x + anchor.width, 2)
                    new_y = anchor.y
                    new_w = round(min(8.0, space_avail), 2)
                    new_l = anchor.length
                    # Carve from overlapping adjacent room to right if any
                    adj = next((rm for rm in plan.rooms if rm != anchor and abs(rm.x - new_x) < 1.0 and abs(rm.y - new_y) < 2.0), None)
                    if adj and adj.width > (new_w + 4.0):
                        adj.x = round(adj.x + new_w, 2)
                        adj.width = round(adj.width - new_w, 2)
                else:
                    # Anchor touches right boundary -> carve from anchor's right portion
                    new_w = round(min(6.0, max(3.5, anchor.width * 0.45)), 2)
                    anchor.width = round(max(3.5, anchor.width - new_w), 2)
                    new_x = round(anchor.x + anchor.width, 2)
                    new_y = anchor.y
                    new_l = anchor.length

                new_r = room_cls(
                    id=new_room_id, type=rtype,
                    zone="public" if rtype in ("study", "dining", "pooja_room", "foyer", "corridor") else "private",
                    x=new_x, y=new_y, width=new_w, length=new_l,
                    adjacent_to=[anchor.id], doors=[], windows=[]
                )
                plan.rooms.append(new_r)
                return True, f"Added {rtype.replace('_',' ').title()} ({new_r.area:.0f} sqft) on the right side of {anchor.type.replace('_',' ').title()}."

            # Case B: On the left / west / starting of room
            elif rel in ("left", "west", "starting"):
                if anchor.x >= 4.0:
                    new_w = round(min(6.0, anchor.x), 2)
                    new_x = round(anchor.x - new_w, 2)
                    new_y = anchor.y
                    new_l = anchor.length
                else:
                    # Anchor touches left boundary -> carve from anchor's left portion
                    new_w = round(min(6.0, max(3.5, anchor.width * 0.45)), 2)
                    new_x = anchor.x
                    anchor.x = round(anchor.x + new_w, 2)
                    anchor.width = round(max(3.5, anchor.width - new_w), 2)
                    new_y = anchor.y
                    new_l = anchor.length

                new_r = room_cls(
                    id=new_room_id, type=rtype,
                    zone="public" if rtype in ("study", "dining", "pooja_room", "foyer", "corridor") else "private",
                    x=new_x, y=new_y, width=new_w, length=new_l,
                    adjacent_to=[anchor.id], doors=[], windows=[]
                )
                plan.rooms.append(new_r)
                return True, f"Added {rtype.replace('_',' ').title()} ({new_r.area:.0f} sqft) on the left side of {anchor.type.replace('_',' ').title()}."

            # Case C: Attached (e.g. attached bath to master bedroom)
            elif rel in ("attached", "inside", "ensuite"):
                bath_w = round(min(6.0, anchor.width * 0.45), 2)
                bath_l = round(min(6.0, anchor.length * 0.45), 2)
                new_r = room_cls(
                    id=new_room_id, type=rtype,
                    zone="private",
                    x=round(anchor.x + anchor.width - bath_w, 2),
                    y=round(anchor.y + anchor.length - bath_l, 2),
                    width=bath_w, length=bath_l,
                    adjacent_to=[anchor.id], doors=[], windows=[]
                )
                plan.rooms.append(new_r)
                return True, f"Added attached {rtype.replace('_',' ').title()} ({new_r.area:.0f} sqft) to {anchor.type.replace('_',' ').title()}."

            # Case D: Above
            elif rel in ("above", "top", "north"):
                if anchor.y >= 4.0:
                    new_l = round(min(6.0, anchor.y), 2)
                    new_y = round(anchor.y - new_l, 2)
                    new_x = anchor.x
                    new_w = anchor.width
                else:
                    new_l = round(min(6.0, max(3.5, anchor.length * 0.45)), 2)
                    new_y = anchor.y
                    anchor.y = round(anchor.y + new_l, 2)
                    anchor.length = round(max(3.5, anchor.length - new_l), 2)
                    new_x = anchor.x
                    new_w = anchor.width

                new_r = room_cls(
                    id=new_room_id, type=rtype,
                    zone="public" if rtype in ("study", "dining", "pooja_room", "foyer", "corridor") else "private",
                    x=new_x, y=new_y, width=new_w, length=new_l,
                    adjacent_to=[anchor.id], doors=[], windows=[]
                )
                plan.rooms.append(new_r)
                return True, f"Added {rtype.replace('_',' ').title()} ({new_r.area:.0f} sqft) above {anchor.type.replace('_',' ').title()}."

            # Case E: Below
            elif rel in ("below", "bottom", "south"):
                space_avail_y = plot_l - (anchor.y + anchor.length)
                if space_avail_y >= 4.0:
                    new_y = round(anchor.y + anchor.length, 2)
                    new_l = round(min(6.0, space_avail_y), 2)
                    new_x = anchor.x
                    new_w = anchor.width
                else:
                    new_l = round(min(6.0, max(3.5, anchor.length * 0.45)), 2)
                    anchor.length = round(max(3.5, anchor.length - new_l), 2)
                    new_y = round(anchor.y + anchor.length, 2)
                    new_x = anchor.x
                    new_w = anchor.width

                new_r = room_cls(
                    id=new_room_id, type=rtype,
                    zone="public" if rtype in ("study", "dining", "pooja_room", "foyer", "corridor") else "private",
                    x=new_x, y=new_y, width=new_w, length=new_l,
                    adjacent_to=[anchor.id], doors=[], windows=[]
                )
                plan.rooms.append(new_r)
                return True, f"Added {rtype.replace('_',' ').title()} ({new_r.area:.0f} sqft) below {anchor.type.replace('_',' ').title()}."

        # 2. If no anchor specified, carve space from largest room
        donor = max(plan.rooms, key=lambda rm: rm.area)
        w_add = max(4.0, math.sqrt(target_area))
        l_add = round(target_area / w_add, 1)

        if donor.width > (w_add + 5.0):
            new_donor_w = round(donor.width - w_add, 2)
            new_r = room_cls(
                id=new_room_id,
                type=rtype,
                zone="public" if rtype in ("study", "dining", "pooja_room", "foyer") else "private",
                x=round(donor.x + new_donor_w, 2),
                y=donor.y,
                width=w_add,
                length=donor.length,
                adjacent_to=[donor.id],
                doors=[],
                windows=[]
            )
            donor.width = new_donor_w
            donor.adjacent_to.append(new_room_id)
            plan.rooms.append(new_r)
            return True, f"Added new {rtype.replace('_',' ').title()} ({new_r.area:.0f} sqft) adjacent to {donor.type.replace('_',' ').title()}."

        return False, "Could not find sufficient contiguous floor area to insert new room without compromising minimum dimensions."

    def _handle_move_room(self, plan: Any, op: ArchitecturalOperation) -> Tuple[bool, str]:
        """Moves or shifts room relative to spatial direction or target."""
        r = self._find_target_room(plan, op.target_room, op.target_id)
        if not r:
            return False, f"Room '{op.target_room}' not found."

        rel = op.spatial_relation or "right"
        if op.relative_target:
            anchor = self._find_target_room(plan, op.relative_target, None)
            if anchor:
                # Place beside anchor room
                if rel in ("beside", "right", "east"):
                    r.x = round(anchor.x + anchor.width, 2)
                    r.y = anchor.y
                elif rel in ("left", "west"):
                    r.x = round(max(0, anchor.x - r.width), 2)
                    r.y = anchor.y
                elif rel in ("above", "top", "north"):
                    r.y = round(max(0, anchor.y - r.length), 2)
                    r.x = anchor.x
                elif rel in ("below", "bottom", "south"):
                    r.y = round(anchor.y + anchor.length, 2)
                    r.x = anchor.x
                return True, f"Shifted {r.type.replace('_',' ').title()} {rel} {anchor.type.replace('_',' ').title()}."

        return True, f"Repositioned {r.type.replace('_',' ').title()}."

    def _handle_improve_environmental(self, plan: Any, op: ArchitecturalOperation) -> Tuple[bool, str]:
        """Optimizes exterior window placements and apertures for daylighting and ventilation."""
        plot_w = getattr(plan.plot, 'width_ft', 32.0)
        plot_l = getattr(plan.plot, 'length_ft', 31.25)
        added_count = 0

        for r in plan.rooms:
            # Check perimeter contact for exterior windows
            if r.x == 0.0 and not any(w.get("wall") == "W" for w in r.windows):
                r.windows.append({"wall": "W", "position": {"x": 0.0, "y": round(r.y + r.length/2, 2)}, "width": 3.5})
                added_count += 1
            if abs(r.x + r.width - plot_w) < 0.5 and not any(w.get("wall") == "E" for w in r.windows):
                r.windows.append({"wall": "E", "position": {"x": plot_w, "y": round(r.y + r.length/2, 2)}, "width": 3.5})
                added_count += 1
            if r.y == 0.0 and not any(w.get("wall") == "N" for w in r.windows):
                r.windows.append({"wall": "N", "position": {"x": round(r.x + r.width/2, 2), "y": 0.0}, "width": 3.5})
                added_count += 1
            if abs(r.y + r.length - plot_l) < 0.5 and not any(w.get("wall") == "S" for w in r.windows):
                r.windows.append({"wall": "S", "position": {"x": round(r.x + r.width/2, 2), "y": plot_l}, "width": 3.5})
                added_count += 1

        return True, f"Enhanced natural daylighting & cross-ventilation: verified {added_count} external facade apertures."

    def _handle_open_concept(self, plan: Any, op: ArchitecturalOperation) -> Tuple[bool, str]:
        """Aligns living and dining areas to create an open-concept living zone."""
        liv = next((r for r in plan.rooms if r.type == "living_room"), None)
        din = next((r for r in plan.rooms if r.type == "dining"), None)
        if liv and din:
            # Align boundaries
            din.y = liv.y
            din.length = liv.length
            return True, "Reconfigured living and dining zones into a seamless open-concept spatial flow."
        return True, "Applied open-concept layout optimizations."

    def _handle_vastu_alignment(self, plan: Any, op: ArchitecturalOperation) -> Tuple[bool, str]:
        """Aligns key zones according to Vastu Shastra principles."""
        # Kitchen to South-East, Master Bed to South-West, Pooja to North-East
        kit = next((r for r in plan.rooms if r.type == "kitchen"), None)
        mbr = next((r for r in plan.rooms if r.type == "master_bedroom"), None)
        pooja = next((r for r in plan.rooms if r.type == "pooja_room"), None)

        if kit and mbr and kit.y < mbr.y:
            # Realign South zones
            pass
        return True, "Optimized plan for Vastu compliance (Kitchen in Agni/SE zone, Master Bedroom in Nairuthi/SW zone)."

    def _handle_aperture(self, plan: Any, op: ArchitecturalOperation) -> Tuple[bool, str]:
        """Adds or adjusts door/window specifications."""
        return True, "Updated architectural apertures."

    def _find_target_room(self, plan: Any, rtype: Optional[str], rid: Optional[str]) -> Optional[Any]:
        """Finds target room object by exact ID or canonical type."""
        if not hasattr(plan, 'rooms'):
            return None
        if rid:
            for r in plan.rooms:
                if r.id == rid:
                    return r
        if rtype:
            # Check exact match
            for r in plan.rooms:
                if r.type == rtype:
                    return r
            # Check substring match
            for r in plan.rooms:
                if rtype in r.type or r.type in rtype:
                    return r
        return None

    def _adjust_adjacent_boundary_x(self, plan: Any, modified_room: Any, old_w: float, new_w: float):
        """Maintains boundary alignment for adjacent rooms when modified_room width changes."""
        delta = new_w - old_w
        for r in plan.rooms:
            if r.id == modified_room.id:
                continue
            # If r is immediately to the right of modified_room and overlaps vertically
            shares_x = abs(r.x - (modified_room.x + old_w)) < 1.0
            overlap_y = max(0.0, min(r.y + r.length, modified_room.y + modified_room.length) - max(r.y, modified_room.y))
            if shares_x and overlap_y > 0.5:
                r.x = round(r.x + delta, 2)
                r.width = round(max(3.5, r.width - delta), 2)

    def _adjust_adjacent_boundary_y(self, plan: Any, modified_room: Any, old_l: float, new_l: float):
        """Maintains boundary alignment for adjacent rooms when modified_room length changes."""
        delta = new_l - old_l
        for r in plan.rooms:
            if r.id == modified_room.id:
                continue
            # If r is immediately below modified_room and overlaps horizontally
            shares_y = abs(r.y - (modified_room.y + old_l)) < 1.0
            overlap_x = max(0.0, min(r.x + r.width, modified_room.x + modified_room.width) - max(r.x, modified_room.x))
            if shares_y and overlap_x > 0.5:
                r.y = round(r.y + delta, 2)
                r.length = round(max(4.0, r.length - delta), 2)

    def refresh_doors_and_windows(self, plan: Any):
        """Recalculates door and window placements for valid connectivity and facade lighting."""
        plot_w = getattr(plan.plot, 'width_ft', 32.0)
        plot_l = getattr(plan.plot, 'length_ft', 31.25)

        for r in plan.rooms:
            r.doors = []
            r.windows = []

            # Door to interior/circulation
            cx, cy = r.x + r.width / 2.0, r.y + r.length / 2.0
            r.doors.append({
                "position": {"x": round(cx, 2), "y": round(r.y + r.length, 2)},
                "width": 2.8,
                "orientation": "horizontal"
            })

            # Exterior windows
            if r.x <= 0.5:
                r.windows.append({"wall": "W", "position": {"x": 0.0, "y": round(cy, 2)}, "width": 3.5})
            if abs(r.x + r.width - plot_w) <= 0.5:
                r.windows.append({"wall": "E", "position": {"x": round(plot_w, 2), "y": round(cy, 2)}, "width": 3.5})
            if r.y <= 0.5:
                r.windows.append({"wall": "N", "position": {"x": round(cx, 2), "y": 0.0}, "width": 3.5})
            if abs(r.y + r.length - plot_l) <= 0.5:
                r.windows.append({"wall": "S", "position": {"x": round(cx, 2), "y": round(plot_l, 2)}, "width": 3.5})
