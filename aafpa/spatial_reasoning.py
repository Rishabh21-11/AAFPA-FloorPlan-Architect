"""
AAFPA 2.0 Spatial Reasoning & Relative Reference Resolver
Resolves spatial directions ('above', 'below', 'left', 'right', 'beside', 'corner')
and topological relationships against the 2D bounding boxes and centroids of active plans.
"""

import math
from typing import Optional, List, Dict, Tuple, Any

class SpatialReasoningEngine:
    """Reasoning engine for spatial topology, relative coordinates, and bounding boxes."""

    @staticmethod
    def get_room_center(room: Any) -> Tuple[float, float]:
        """Calculates (cx, cy) center of a room."""
        return room.x + room.width / 2.0, room.y + room.length / 2.0

    @classmethod
    def find_room_by_spatial_relation(cls, rooms: List[Any], relation: str,
                                     anchor_room: Optional[Any] = None,
                                     target_type: Optional[str] = None) -> Optional[Any]:
        """
        Finds the best room matching a spatial relation (e.g. 'above the bathroom', 'rightmost bedroom').
        """
        if not rooms:
            return None

        # Filter candidate rooms by type if specified
        candidates = rooms
        if target_type:
            filtered = [r for r in rooms if r.type == target_type or target_type in r.type]
            if filtered:
                candidates = filtered

        # If relation is relative to an anchor room
        if anchor_room:
            ax, ay = cls.get_room_center(anchor_room)
            valid_relative = []

            for r in candidates:
                if r.id == anchor_room.id:
                    continue
                cx, cy = cls.get_room_center(r)
                dx = cx - ax
                dy = cy - ay
                dist = math.hypot(dx, dy)

                if relation in ("above", "top", "upper", "north"):
                    # dy is negative in top-down screen coordinates (or cy < ay)
                    if cy < ay + 1.0:
                        valid_relative.append((dist, r))
                elif relation in ("below", "bottom", "lower", "south"):
                    if cy > ay - 1.0:
                        valid_relative.append((dist, r))
                elif relation in ("left", "west"):
                    if cx < ax + 1.0:
                        valid_relative.append((dist, r))
                elif relation in ("right", "east"):
                    if cx > ax - 1.0:
                        valid_relative.append((dist, r))
                elif relation in ("beside", "adjacent", "next to", "near"):
                    valid_relative.append((dist, r))

            if valid_relative:
                valid_relative.sort(key=lambda x: x[0])
                return valid_relative[0][1]

        # Absolute spatial relations (e.g. "upper bedroom", "bottom right corner")
        if relation in ("above", "top", "upper", "north"):
            return min(candidates, key=lambda r: r.y)
        elif relation in ("below", "bottom", "lower", "south"):
            return max(candidates, key=lambda r: r.y + r.length)
        elif relation in ("left", "west"):
            return min(candidates, key=lambda r: r.x)
        elif relation in ("right", "east"):
            return max(candidates, key=lambda r: r.x + r.width)
        elif relation in ("corner", "northeast"):
            return min(candidates, key=lambda r: r.x + (1000 - r.y))
        elif relation in ("center", "middle"):
            avg_x = sum(r.x + r.width / 2.0 for r in rooms) / len(rooms)
            avg_y = sum(r.y + r.length / 2.0 for r in rooms) / len(rooms)
            return min(candidates, key=lambda r: math.hypot(r.x + r.width / 2.0 - avg_x, r.y + r.length / 2.0 - avg_y))

        return candidates[0] if candidates else None

    @classmethod
    def get_adjacent_rooms(cls, target_room: Any, all_rooms: List[Any], tolerance: float = 1.0) -> List[Any]:
        """Finds rooms that physically touch or share a boundary segment with target_room."""
        adj = []
        tx1, ty1 = target_room.x, target_room.y
        tx2, ty2 = tx1 + target_room.width, ty1 + target_room.length

        for r in all_rooms:
            if r.id == target_room.id:
                continue
            rx1, ry1 = r.x, r.y
            rx2, ry2 = rx1 + r.width, ry1 + r.length

            # Check horizontal boundary sharing
            shares_x = max(0, min(tx2, rx2) - max(tx1, rx1)) > 0.5
            touches_y = abs(ty1 - ry2) <= tolerance or abs(ty2 - ry1) <= tolerance

            # Check vertical boundary sharing
            shares_y = max(0, min(ty2, ry2) - max(ty1, ry1)) > 0.5
            touches_x = abs(tx1 - rx2) <= tolerance or abs(tx2 - rx1) <= tolerance

            if (shares_x and touches_y) or (shares_y and touches_x):
                adj.append(r)

        return adj
