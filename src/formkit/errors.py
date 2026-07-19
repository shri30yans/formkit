"""formkit errors — failed features must not silently no-op."""

from __future__ import annotations


class FormkitError(Exception):
    """Base error for formkit."""


class FeatureError(FormkitError):
    """A timeline feature failed during rebuild."""

    def __init__(self, index: int, kind: str, message: str) -> None:
        self.index = index
        self.kind = kind
        self.message = message
        super().__init__(f"Feature[{index}] {kind}: {message}")


class ValidationError(FormkitError):
    """Printability / input validation failed."""
