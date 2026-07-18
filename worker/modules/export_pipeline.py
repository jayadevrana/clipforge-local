from __future__ import annotations

from pathlib import Path

from .layout_strategy import analyze_layout
from .subtitle_renderer import build_subtitle_assets
from .utils import run_command, slugify
from .vertical_reframe import build_base_filter


def export_clip(job_dir: Path, source_video: Path, transcript: dict, clip: dict) -> dict:
    exports_dir = job_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    layout = analyze_layout(job_dir, source_video, clip, transcript)
    subtitle_manifest = build_subtitle_assets(job_dir, clip, transcript, clip["subtitlePreset"], layout)
    base_filter, base_label = build_base_filter(layout, clip["duration"])
    safe_name = slugify(clip["title"], clip["id"])
    output_path = exports_dir / f"{clip['id']}-{safe_name}.mp4"
    input_args = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{clip['start']:.3f}",
        "-t",
        f"{clip['duration']:.3f}",
        "-i",
        str(source_video),
    ]
    for overlay in subtitle_manifest["overlays"]:
        input_args.extend(["-loop", "1", "-i", overlay["path"]])

    filter_parts = [base_filter]
    final_label = base_label
    for index, overlay in enumerate(subtitle_manifest["overlays"], start=1):
        next_label = f"v{index}"
        filter_parts.append(
            f"[{final_label}][{index}:v]overlay=x=(W-w)/2:y={overlay['y']}:enable='between(t,{overlay['start']:.3f},{overlay['end']:.3f})'[{next_label}]"
        )
        final_label = next_label

    base_args = input_args + [
        "-filter_complex",
        ";".join(filter_parts),
        "-map",
        f"[{final_label}]",
        "-map",
        "0:a:0?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-movflags",
        "+faststart",
        "-shortest",
    ]

    try:
        run_command(base_args + ["-c:a", "copy", str(output_path)])
    except Exception:
        run_command(base_args + ["-c:a", "aac", "-b:a", "192k", str(output_path)])

    clip["outputPath"] = str(output_path)
    clip["subtitlePath"] = subtitle_manifest["overlays"][0]["path"] if subtitle_manifest["overlays"] else None
    clip["baseFilter"] = base_filter
    clip["baseFilterOutput"] = base_label
    clip["finalFilter"] = ";".join(filter_parts)
    clip["layoutMode"] = layout["mode"]
    clip["layoutNotes"] = layout["notes"]
    clip["layoutPath"] = str(job_dir / "tmp" / clip["id"] / "layout" / "layout-analysis.json")
    clip["ocrProtectedBoxCount"] = len(layout["protectedBoxes"])
    clip["subtitleY"] = subtitle_manifest["subtitleY"]
    clip["titleY"] = subtitle_manifest["titleY"]
    clip["status"] = "exporting"
    return clip
