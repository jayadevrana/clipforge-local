from __future__ import annotations

from .boundary_refiner import detect_clips as detect_clips_with_boundaries


def detect_clips(transcript: dict) -> list[dict]:
    return detect_clips_with_boundaries(transcript)
