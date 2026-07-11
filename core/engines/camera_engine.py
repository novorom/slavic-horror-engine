from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CameraMove:
    start_zoom: float
    end_zoom: float
    start_center: tuple[float, float]
    end_center: tuple[float, float]


class CameraEngine:
    def move_for_scene(self, index: int) -> CameraMove:
        centers = [
            ((0.50, 0.50), (0.46, 0.48)),
            ((0.46, 0.52), (0.56, 0.48)),
            ((0.54, 0.46), (0.50, 0.56)),
            ((0.50, 0.56), (0.48, 0.44)),
        ]
        start, end = centers[index % len(centers)]
        if index % 2 == 0:
            return CameraMove(1.0, 1.085, start, end)
        return CameraMove(1.085, 1.0, start, end)

    def interpolate(self, move: CameraMove, t: float, duration: float) -> tuple[float, float, float]:
        progress = 0.0 if duration <= 0 else max(0.0, min(t / duration, 1.0))
        eased = 0.5 - 0.5 * math.cos(progress * math.pi)
        zoom = move.start_zoom + (move.end_zoom - move.start_zoom) * eased
        cx = move.start_center[0] + (move.end_center[0] - move.start_center[0]) * eased
        cy = move.start_center[1] + (move.end_center[1] - move.start_center[1]) * eased
        return zoom, cx, cy
