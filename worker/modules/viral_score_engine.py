from __future__ import annotations

import math
import re


HOOK_TERMS = {
    "why": "Strong Hook",
    "how": "Useful Advice",
    "mistake": "Useful Advice",
    "secret": "Strong Hook",
    "never": "Controversial Take",
    "always": "Strong Hook",
    "warning": "Strong Hook",
    "truth": "Controversial Take",
    "important": "High Retention Opening",
    "best": "Useful Advice",
}

EMOTION_TERMS = {
    "amazing": "Emotional Moment",
    "crazy": "Emotional Moment",
    "surprising": "Emotional Moment",
    "fear": "Emotional Moment",
    "love": "Emotional Moment",
    "hate": "Controversial Take",
    "shocking": "Emotional Moment",
}

PAYOFF_TERMS = {"so", "therefore", "finally", "because", "that is why", "the point is"}
FILLER_TERMS = {"um", "uh", "like", "you know", "sort of", "kind of"}
TRANSITION_STARTS = ("and ", "but ", "so ", "then ", "because ")


def score_segment(text: str, duration: float) -> tuple[int, list[str]]:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    words = [word for word in re.split(r"\s+", normalized) if word]
    opening = words[:14]

    score = 44.0
    reasons: list[str] = []

    density = len(words) / max(duration, 1.0)
    score += min(16.0, max(0.0, (density - 1.7) * 8))

    for term, tag in HOOK_TERMS.items():
        if term in " ".join(opening):
            score += 8
            reasons.append(tag)

    for term, tag in EMOTION_TERMS.items():
        if term in normalized:
            score += 5
            reasons.append(tag)

    if any(term in normalized for term in PAYOFF_TERMS):
        score += 6
        reasons.append("Story Payoff")

    if re.search(r"\b(3|5|7|10|first|second|third)\b", normalized):
        score += 5
        reasons.append("Useful Advice")

    if normalized.endswith("?") or "?" in text:
        score += 5
        reasons.append("Strong Hook")

    if len(words) >= 90:
        score += 5

    if not normalized.startswith(TRANSITION_STARTS):
        score += 6
        reasons.append("High Retention Opening")
    else:
        score -= 8

    filler_count = sum(normalized.count(term) for term in FILLER_TERMS)
    score -= min(10.0, filler_count * 1.5)

    unique_ratio = len(set(words)) / max(len(words), 1)
    score += min(8.0, unique_ratio * 10.0)

    final_score = max(0, min(100, int(round(score))))
    deduped_reasons: list[str] = []
    for reason in reasons:
        if reason not in deduped_reasons:
            deduped_reasons.append(reason)

    if not deduped_reasons:
        deduped_reasons = ["High Retention Opening"]

    return final_score, deduped_reasons[:4]


def build_clip_title(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return "Untitled clip"

    words = normalized.split(" ")
    title = " ".join(words[:10]).strip()
    if len(words) > 10:
        title += "..."
    return title

