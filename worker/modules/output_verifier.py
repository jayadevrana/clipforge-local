from __future__ import annotations

import json
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image

from .boundary_refiner import BAD_STARTS, CONTEXT_DEPENDENT_OPENERS, build_sentence_units
from .layout_strategy import important_text_preserved
from .utils import read_json, run_command, write_json


def _ffprobe(path: Path) -> dict:
    raw = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(path),
        ],
        capture_output=True,
    )
    return json.loads(raw)


def _audio_similarity(source_video: Path, output_video: Path, clip: dict) -> float:
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        source_wav = tmp_dir / "source.wav"
        output_wav = tmp_dir / "output.wav"

        run_command(
            [
                "ffmpeg",
                "-y",
                "-ss",
                f"{clip['start']:.3f}",
                "-t",
                f"{clip['duration']:.3f}",
                "-i",
                str(source_video),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                str(source_wav),
            ]
        )
        run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(output_video),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                str(output_wav),
            ]
        )

        with wave.open(str(source_wav), "rb") as source_file:
            source_samples = np.frombuffer(source_file.readframes(source_file.getnframes()), dtype=np.int16).astype(np.float32)

        with wave.open(str(output_wav), "rb") as output_file:
            output_samples = np.frombuffer(output_file.readframes(output_file.getnframes()), dtype=np.int16).astype(np.float32)

    length = min(len(source_samples), len(output_samples))
    if length < 1000:
        return 0.0

    source_samples = source_samples[:length]
    output_samples = output_samples[:length]
    source_samples -= source_samples.mean()
    output_samples -= output_samples.mean()
    denominator = np.linalg.norm(source_samples) * np.linalg.norm(output_samples)
    if denominator == 0:
        return 0.0
    return float(np.dot(source_samples, output_samples) / denominator)


def _subtitle_diff(source_video: Path, output_video: Path, clip: dict, transcript: dict) -> tuple[bool, float]:
    clip_start = clip["start"]
    clip_end = clip["end"]
    candidate_times = []
    for cue in transcript["cues"]:
        if cue["end"] < clip_start or cue["start"] > clip_end:
            continue
        midpoint = max(0.5, min(clip["duration"] - 0.5, ((cue["start"] + cue["end"]) / 2.0) - clip_start))
        if 3.0 <= midpoint <= clip["duration"] - 1.0:
            candidate_times.append(round(midpoint, 3))
        if len(candidate_times) >= 3:
            break

    if not candidate_times:
        candidate_times = [min(max(3.5, clip["duration"] / 2.0), max(0.8, clip["duration"] - 0.8))]

    diffs = []
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        for index, relative_time in enumerate(candidate_times):
            source_frame = tmp_dir / f"source-{index}.png"
            output_frame = tmp_dir / f"output-{index}.png"
            source_timestamp = clip_start + relative_time

            run_command(
                [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    f"{source_timestamp:.3f}",
                    "-i",
                    str(source_video),
                    "-frames:v",
                    "1",
                    "-update",
                    "1",
                    "-filter_complex",
                    clip["baseFilter"],
                    "-map",
                    f"[{clip['baseFilterOutput']}]",
                    str(source_frame),
                ]
            )
            run_command(
                [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    f"{relative_time:.3f}",
                    "-i",
                    str(output_video),
                    "-frames:v",
                    "1",
                    "-update",
                    "1",
                    str(output_frame),
                ]
            )

            baseline = np.asarray(Image.open(source_frame).convert("RGB"), dtype=np.int16)
            rendered = np.asarray(Image.open(output_frame).convert("RGB"), dtype=np.int16)
            start_row = int(rendered.shape[0] * 0.55)
            diff = np.abs(rendered[start_row:, :, :] - baseline[start_row:, :, :]).mean()
            diffs.append(float(diff))

    average_diff = float(sum(diffs) / len(diffs))
    return average_diff >= 7.5, average_diff


def _boundary_quality(clip: dict, transcript: dict) -> tuple[bool, list[str]]:
    notes: list[str] = []
    sentences = build_sentence_units(transcript["cues"])
    overlapping = [sentence for sentence in sentences if sentence.end >= clip["start"] and sentence.start <= clip["end"]]
    if not overlapping:
        return False, ["No sentence-aligned transcript span was found for the clip boundaries."]

    first_sentence = overlapping[0]
    last_sentence = overlapping[-1]
    start_offset = max(0.0, first_sentence.start - clip["start"])
    end_offset = max(0.0, clip["end"] - last_sentence.end)
    opener_tokens = first_sentence.text.split()
    opener = opener_tokens[0].lower().strip(",.!?") if opener_tokens else ""
    last_tokens = [token.lower().strip(",.!?") for token in last_sentence.text.split() if token.strip()]
    last_token = last_tokens[-1] if last_tokens else ""
    sentence_complete = last_sentence.text.rstrip().endswith((".", "!", "?")) or (
        len(last_tokens) >= 8 and last_token not in BAD_STARTS and last_token not in {"and", "or", "then"}
    )
    opener_contextual = opener in BAD_STARTS or opener in CONTEXT_DEPENDENT_OPENERS

    if start_offset <= 0.65:
        notes.append(f"Start reaches the next sentence boundary within {start_offset:.2f}s.")
    else:
        notes.append(f"Start takes {start_offset:.2f}s to reach a sentence boundary, which feels too abrupt.")

    if end_offset <= 0.8:
        notes.append(f"End leaves {end_offset:.2f}s after the last sentence for the point to land.")
    else:
        notes.append(f"End trails the last sentence by {end_offset:.2f}s, which may feel padded or unresolved.")

    if opener_contextual:
        notes.append("Opening phrase still depends on previous context.")
    else:
        notes.append("Opening phrase reads as a standalone setup or hook.")

    if sentence_complete:
        notes.append("Closing sentence resolves cleanly for a standalone short.")
    else:
        notes.append("Closing sentence may not resolve cleanly.")

    passed = start_offset <= 0.65 and end_offset <= 0.8 and not opener_contextual and sentence_complete
    return passed, notes


def verify_clip(job_dir: Path, source_video: Path, transcript: dict, clip: dict) -> dict:
    output_video = Path(clip["outputPath"])
    notes: list[str] = []

    if not output_video.exists():
        raise RuntimeError(f"Missing exported clip at {output_video}")

    playable = True
    try:
        run_command(["ffmpeg", "-v", "error", "-i", str(output_video), "-f", "null", "-"])
        notes.append("FFmpeg decode test passed.")
    except Exception:
        playable = False
        notes.append("FFmpeg decode test failed.")

    probe = _ffprobe(output_video)
    streams = probe.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    duration = float(probe.get("format", {}).get("duration", 0.0))

    aspect_ratio_valid = abs((width / max(height, 1)) - (9 / 16)) <= 0.02
    duration_valid = 30.0 <= duration <= 90.5
    resolution_valid = width >= 540 and height >= 960
    audio_stream_present = audio_stream is not None

    if aspect_ratio_valid:
        notes.append("Aspect ratio is within 9:16 tolerance.")
    else:
        notes.append("Aspect ratio is not valid for vertical short-form export.")

    if duration_valid:
        notes.append("Duration is within the 30s-90s target.")
    else:
        notes.append("Duration is outside the 30s-90s target.")

    if audio_stream_present:
        notes.append("Audio stream present.")
    else:
        notes.append("Audio stream missing.")

    audio_similarity = _audio_similarity(source_video, output_video, clip) if audio_stream_present else 0.0
    notes.append(f"Audio similarity to original section: {audio_similarity:.3f}.")

    subtitle_burned_in, subtitle_diff_score = _subtitle_diff(source_video, output_video, clip, transcript)
    if subtitle_burned_in:
        notes.append("Subtitle burn-in was confirmed via frame diff sampling.")
    else:
        notes.append("Subtitle burn-in could not be confirmed via frame diff sampling.")

    clean_boundaries, boundary_notes = _boundary_quality(clip, transcript)
    notes.extend(boundary_notes)

    important_text_ok = True
    if clip.get("layoutPath"):
        layout = read_json(Path(clip["layoutPath"]))
        important_text_ok = important_text_preserved(layout)
        if important_text_ok:
            notes.append(f"Protected OCR text remained readable in {layout['mode']} mode.")
        else:
            notes.append(f"Protected OCR text would be clipped in {layout['mode']} mode.")

    passed = all(
        [
            playable,
            aspect_ratio_valid,
            duration_valid,
            audio_stream_present,
            audio_similarity >= 0.90,
            subtitle_burned_in,
            resolution_valid,
            clean_boundaries,
            important_text_ok,
        ]
    )

    report = {
        "filename": output_video.name,
        "duration": round(duration, 3),
        "width": width,
        "height": height,
        "aspectRatioValid": aspect_ratio_valid,
        "audioStreamPresent": audio_stream_present,
        "audioSimilarity": round(audio_similarity, 4),
        "subtitleBurnedIn": subtitle_burned_in,
        "subtitleDiffScore": round(subtitle_diff_score, 4),
        "playable": playable,
        "durationValid": duration_valid,
        "resolutionValid": resolution_valid,
        "cleanBoundaries": clean_boundaries,
        "importantTextPreserved": important_text_ok,
        "layoutMode": clip.get("layoutMode"),
        "passed": passed,
        "notes": notes,
        "verifiedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }

    write_json(output_video.with_suffix(".verification.json"), report)
    return report
