from __future__ import annotations

import json
import re
from pathlib import Path

from .utils import clean_text, python_yt_dlp_args, read_json, run_command, write_json


def _parse_json3(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    events = payload.get("events", [])
    cues: list[dict] = []

    for event in events:
        segs = event.get("segs")
        if not segs:
            continue

        text = clean_text("".join(seg.get("utf8", "") for seg in segs))
        text = text.replace("♪", "").strip()

        if not text:
            continue

        start = max(0.0, event.get("tStartMs", 0) / 1000.0)
        duration = max(0.35, event.get("dDurationMs", 1400) / 1000.0)
        end = start + duration

        if cues and text == cues[-1]["text"]:
            continue

        if cues and text.startswith(cues[-1]["text"]):
            delta = text[len(cues[-1]["text"]) :].strip()
            if delta:
                text = delta
            else:
                continue

        cues.append(
            {
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": round(duration, 3),
                "text": text,
                "words": text.split(),
            }
        )

    return cues


def _parse_vtt(path: Path) -> list[dict]:
    blocks = path.read_text(encoding="utf-8").split("\n\n")
    cues: list[dict] = []

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        timestamp_line = next((line for line in lines if "-->" in line), None)
        if not timestamp_line:
            continue

        text_lines = [line for line in lines if "-->" not in line and not line.startswith("WEBVTT")]
        text = clean_text(" ".join(text_lines))
        if not text:
            continue

        left, right = [part.strip().split(" ")[0] for part in timestamp_line.split("-->")]
        start = _vtt_timestamp_to_seconds(left)
        end = _vtt_timestamp_to_seconds(right)

        cues.append(
            {
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": round(max(0.35, end - start), 3),
                "text": text,
                "words": text.split(),
            }
        )

    return cues


def _vtt_timestamp_to_seconds(value: str) -> float:
    time_part, milliseconds = value.split(".")
    parts = [int(part) for part in time_part.split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
        hours = 0
    else:
        hours, minutes, seconds = parts
    return hours * 3600 + minutes * 60 + seconds + int(milliseconds) / 1000.0


def _try_caption_download(url: str, source_dir: Path, subtitle_format: str) -> list[Path]:
    output_template = source_dir / "captions.%(ext)s"
    try:
        run_command(
            python_yt_dlp_args()
            + [
                "--no-playlist",
                "--skip-download",
                "--write-auto-subs",
                "--write-subs",
                "--sub-langs",
                "en.*",
                "--sub-format",
                subtitle_format,
                "-o",
                str(output_template),
                url,
            ]
        )
        return sorted(source_dir.glob(f"captions*.{subtitle_format}"))
    except Exception:
        return []


def _fallback_whisper(video_path: Path) -> list[dict]:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception as exc:  # pragma: no cover - optional fallback
        raise RuntimeError(
            "No downloadable subtitle track was found and faster-whisper is not installed for fallback transcription."
        ) from exc

    model = WhisperModel("tiny.en", device="cpu", compute_type="int8", download_root="/tmp/clipforge-models")
    segments, _ = model.transcribe(str(video_path), word_timestamps=False)
    cues: list[dict] = []
    for segment in segments:
        text = clean_text(segment.text)
        if not text:
            continue
        cues.append(
            {
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "duration": round(max(0.35, segment.end - segment.start), 3),
                "text": text,
                "words": text.split(),
            }
        )
    return cues


def extract_transcript(job_dir: Path, url: str, video_path: Path) -> dict:
    source_dir = job_dir / "source"
    transcript_path = source_dir / "transcript.json"

    if transcript_path.exists():
        cached = read_json(transcript_path)
        if cached.get("cues"):
            return cached

    cues: list[dict] = []
    json3_files = _try_caption_download(url, source_dir, "json3")

    if json3_files:
        cues = _parse_json3(json3_files[0])

    if not cues:
        vtt_files = _try_caption_download(url, source_dir, "vtt")
        if vtt_files:
            cues = _parse_vtt(vtt_files[0])

    if not cues:
        cues = _fallback_whisper(video_path)

    if not cues:
        raise RuntimeError("Transcript extraction finished without any timed cues.")

    full_text = " ".join(cue["text"] for cue in cues)
    transcript = {
        "cues": cues,
        "preview": full_text[:320].strip(),
        "wordCount": sum(len(cue["words"]) for cue in cues),
        "estimatedDuration": round(max(cue["end"] for cue in cues), 3),
    }

    write_json(transcript_path, transcript)
    return transcript
