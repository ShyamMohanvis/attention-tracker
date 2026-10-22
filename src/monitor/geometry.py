"""
monitor/geometry.py — Data class for a single physical monitor's geometry.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonitorGeometry:
    """
    Physical monitor descriptor.

    Attributes:
        index:     1-based monitor number (matches settings.video_monitor).
        x, y:     Top-left corner in virtual screen coordinates.
        width:     Width in pixels.
        height:    Height in pixels.
        is_primary: True for the main/primary display.
    """

    index: int
    x: int
    y: int
    width: int
    height: int
    is_primary: bool = False

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def center_x(self) -> int:
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        return self.y + self.height // 2

    def contains(self, screen_x: int, screen_y: int) -> bool:
        """True if the point falls within this monitor's bounding rectangle."""
        return self.x <= screen_x < self.right and self.y <= screen_y < self.bottom

    def __str__(self) -> str:
        primary = " [Primary]" if self.is_primary else ""
        return f"Monitor {self.index}{primary} ({self.width}×{self.height} @ {self.x},{self.y})"
