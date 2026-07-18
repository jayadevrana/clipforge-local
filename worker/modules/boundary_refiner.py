from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .viral_score_engine import build_clip_title, score_segment


TARGET_DURATIONS = [34, 42, 52, 66, 78]
BAD_STARTS = {
    "so",
    "and",
    "but",
    "then",
    "because",
    "also",
    "anyway",
    "well",
}
CONTEXT_DEPENDENT_OPENERS = {
    "this",
    "that",
    "it",
    "these",
    "those",
    "they",
}
HOOK_MARKERS = {
    "how",
    "why",
    "what",
    "whenever",
    "important",
    "simple",
    "never",
    "best",
}


@dataclass
class SentenceUnit:
    start: float
    end: float
    text: str
    cue_start_index: int
    cue_end_index: int

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class CandidateClip:
    start: float
    end: float
    duration: float
    text: str
    title: str
    score: int
    reason_tags: list[str]
    layout_hints: list[str]
    boundary_notes: list[str]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def build_sentence_units(cues: list[dict]) -> list[SentenceUnit]:
    sentences: list[SentenceUnit] = []
    buffer_text: list[str] = []
    buffer_start = None
    buffer_cue_start = 0

    for index, cue in enumerate(cues):
        text = _normalize(cue["text"])
        if not text:
            continue

        if buffer_start is None:
            buffer_start = cue["start"]
            buffer_cue_start = index

        buffer_text.append(text)
        next_gap = 0.0
        if index < len(cues) - 1:
            next_gap = max(0.0, cues[index + 1]["start"] - cue["end"])

        should_close = text.endswith((".", "!", "?")) or next_gap >= 0.55 or len(" ".join(buffer_text).split()) >= 34
        if should_close:
            sentence_text = _normalize(" ".join(buffer_text))
            sentences.append(
                SentenceUnit(
                    start=buffer_start,
                    end=cue["end"],
                    text=sentence_text,
                    cue_start_index=buffer_cue_start,
                    cue_end_index=index,
                )
            )
            buffer_text = []
            buffer_start = None

    if buffer_text and buffer_start is not None:
        sentence_text = _normalize(" ".join(buffer_text))
        sentences.append(
            SentenceUnit(
                start=buffer_start,
                end=cues[-1]["end"],
                text=sentence_text,
                cue_start_index=buffer_cue_start,
                cue_end_index=len(cues) - 1,
            )
        )

    return sentences


def _candidate_penalty(text: str, duration: float) -> tuple[int, list[str]]:
    words = text.split()
    if not words:
        return 20, ["Empty candidate"]

    penalties = 0
    notes: list[str] = []
    opener = words[0].lower().strip(",.!?")

    if opener in BAD_STARTS:
        penalties += 15
        notes.append("Starts on a weak transition word")

    if opener in CONTEXT_DEPENDENT_OPENERS:
        penalties += 8
        notes.append("Opening depends on previous context")

    if duration < 32:
        penalties += 8
        notes.append("Too short to fully land the idea")

    if text.count(".") + text.count("!") + text.count("?") < 1:
        penalties += 5
        notes.append("Feels less sentence-complete")

    return penalties, notes


def _candidate_bonus(text: str, first_sentence: str, last_sentence: str, duration: float) -> tuple[int, list[str]]:
    bonus = 0
    notes: list[str] = []
    opening_words = first_sentence.lower().split()[:12]
    opening_phrase = " ".join(opening_words)

    if any(marker in opening_phrase for marker in HOOK_MARKERS):
        bonus += 10
        notes.append("Strong opening hook")

    if last_sentence.endswith((".", "!", "?")):
        bonus += 6
        notes.append("Ends on a completed statement")

    if any(token in last_sentence.lower() for token in {"therefore", "because", "that's why", "simple", "important"}):
        bonus += 5
        notes.append("Contains a payoff or takeaway")

    word_count = len(text.split())
    if word_count / max(duration, 1.0) >= 1.8:
        bonus += 4
        notes.append("High information density")

    return bonus, notes


def _refine_boundaries(sentences: list[SentenceUnit], start_index: int, end_index: int, cues: list[dict]) -> tuple[float, float, list[str]]:
    first = sentences[start_index]
    last = sentences[end_index]
    notes: list[str] = []

    gap_before = first.start - cues[first.cue_start_index - 1]["end"] if first.cue_start_index > 0 else 0.0
    gap_after = cues[last.cue_end_index + 1]["start"] - last.end if last.cue_end_index < len(cues) - 1 else 0.0

    lead_in = min(0.45, max(0.0, gap_before * 0.45))
    tail_out = min(0.55, max(0.0, gap_after * 0.55))

    start = max(0.0, first.start - lead_in)
    end = last.end + tail_out

    if lead_in > 0.05:
        notes.append(f"Added {lead_in:.2f}s lead-in at a natural pause.")
    else:
        notes.append("Start aligned to a sentence boundary without extra filler.")

    if tail_out > 0.05:
        notes.append(f"Added {tail_out:.2f}s tail-out so the closing thought can land.")
    else:
        notes.append("End aligned to a completed sentence without clipping the finish.")

    return round(start, 3), round(end, 3), notes


def _overlap_ratio(a: CandidateClip, b: CandidateClip) -> float:
    overlap = max(0.0, min(a.end, b.end) - max(a.start, b.start))
    if overlap <= 0:
        return 0.0
    return overlap / min(a.duration, b.duration)


def detect_clips(transcript: dict) -> list[dict]:
    cues: list[dict] = transcript["cues"]
    if len(cues) < 2:
        raise RuntimeError("Not enough transcript cues were extracted to build clips.")

    sentences = build_sentence_units(cues)
    if not sentences:
        raise RuntimeError("Unable to derive sentence units from the transcript.")

    candidates: list[CandidateClip] = []
    for start_index in range(len(sentences)):
        combined_text: list[str] = []
        for end_index in range(start_index, len(sentences)):
            combined_text.append(sentences[end_index].text)
            start, end, boundary_notes = _refine_boundaries(sentences, start_index, end_index, cues)
            duration = round(end - start, 3)

            if duration < 30:
                continue
            if duration > 90:
                break

            opener = sentences[start_index].text.split()[0].lower().strip(",.!?") if sentences[start_index].text.split() else ""
            if start_index > 0 and opener in BAD_STARTS.union(CONTEXT_DEPENDENT_OPENERS):
                continue

            text = _normalize(" ".join(combined_text))
            if len(text.split()) < 45:
                continue

            base_score, reason_tags = score_segment(text, duration)
            penalties, penalty_notes = _candidate_penalty(sentences[start_index].text, duration)
            bonuses, bonus_notes = _candidate_bonus(text, sentences[start_index].text, sentences[end_index].text, duration)
            score = max(0, min(100, base_score + bonuses - penalties))

            candidates.append(
                CandidateClip(
                    start=start,
                    end=end,
                    duration=duration,
                    text=text,
                    title=build_clip_title(text),
                    score=score,
                    reason_tags=reason_tags,
                    layout_hints=[
                        "Finance layout preserve readability"
                        if any(token in text.lower() for token in {"indicator", "chart", "oscillator", "market", "ema", "candle"})
                        else "General spoken content"
                    ],
                    boundary_notes=boundary_notes + bonus_notes + penalty_notes,
                )
            )

    if not candidates:
        raise RuntimeError("Moment detection could not find any clip candidates in the transcript.")

    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    selected: list[CandidateClip] = []
    for candidate in candidates:
        if all(_overlap_ratio(candidate, existing) < 0.5 for existing in selected):
            selected.append(candidate)
        if len(selected) >= 5:
            break

    if len(selected) < 3:
        for candidate in candidates:
            if candidate not in selected:
                selected.append(candidate)
            if len(selected) >= min(3, len(candidates)):
                break

    subtitle_cycle = ["bold-viral", "creator-neon", "clean-minimal"]
    clips = []
    for index, candidate in enumerate(selected):
        clips.append(
            {
                "id": f"clip-{index + 1}",
                "title": candidate.title,
                "start": round(candidate.start, 3),
                "end": round(candidate.end, 3),
                "duration": round(candidate.duration, 3),
                "score": candidate.score,
                "reasonTags": candidate.reason_tags,
                "subtitlePreset": subtitle_cycle[index % len(subtitle_cycle)],
                "boundaryNotes": candidate.boundary_notes,
                "layoutHints": candidate.layout_hints,
            }
        )

    return clips
