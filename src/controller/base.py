"""
controller/base.py — Abstract base class for all media controllers.

Every concrete controller must implement play() and pause().
Each returns True on success so the CompositeController knows whether to
fall through to the next controller in the priority chain.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class MediaController(ABC):
    """Abstract media controller interface."""

    @abstractmethod
    def play(self) -> bool:
        """Send a play command.  Returns True if successfully delivered."""
        ...

    @abstractmethod
    def pause(self) -> bool:
        """Send a pause command.  Returns True if successfully delivered."""
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"<{self.name}>"


class CompositeMediaController(MediaController):
    """
    Tries a list of controllers in priority order.

    Stops at the first controller that returns True.  This implements the
    priority chain:
        WindowsMediaSessionController → MediaKeyController → FocusedWindowController
    """

    def __init__(self, controllers: list[MediaController]) -> None:
        self._controllers = controllers

    def play(self) -> bool:
        for ctrl in self._controllers:
            try:
                if ctrl.play():
                    return True
            except Exception:
                pass
        return False

    def pause(self) -> bool:
        for ctrl in self._controllers:
            try:
                if ctrl.pause():
                    return True
            except Exception:
                pass
        return False

    @property
    def controller_names(self) -> list[str]:
        return [c.name for c in self._controllers]
