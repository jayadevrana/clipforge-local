from __future__ import annotations

import sys
import json
from datetime import datetime
from pathlib import Path

from modules.export_pipeline import export_clip
from modules.job_store import job_dir, load_job, save_job, set_stage
from modules.output_verifier import verify_clip


def main(job_id: str, clip_id: str, trim_start_seconds: float, trim_end_seconds: float, subtitle_preset: str) -> None:
    job = load_job(job_id)
    current_dir = job_dir(job_id)
    transcript_path = current_dir / "source" / "transcript.json"
    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    source_video = Path(job["sourceVideoPath"])
    clip = next((item for item in job["clips"] if item["id"] == clip_id), None)
    if not clip:
        raise RuntimeError("Clip not found for re-export.")

    new_start = clip["start"] + trim_start_seconds
    new_end = clip["end"] - trim_end_seconds
    new_duration = round(new_end - new_start, 3)

    if new_duration < 30 or new_duration > 90:
        raise RuntimeError("Trim adjustments must keep the clip between 30 and 90 seconds.")

    clip["start"] = round(new_start, 3)
    clip["end"] = round(new_end, 3)
    clip["duration"] = new_duration
    clip["subtitlePreset"] = subtitle_preset
    clip["status"] = "exporting"
    clip["updatedAt"] = datetime.utcnow().isoformat() + "Z"
    save_job(job)

    set_stage(job_id, "exporting", f"Re-exporting {clip['title']} with updated trims and subtitle preset.", 78)
    job = load_job(job_id)
    clip = next((item for item in job["clips"] if item["id"] == clip_id), None)
    export_clip(current_dir, source_video, transcript, clip)
    save_job(job)
    set_stage(job_id, "verifying", f"Re-running verification for {clip['title']}.", 92)
    job = load_job(job_id)
    clip = next((item for item in job["clips"] if item["id"] == clip_id), None)
    report = verify_clip(current_dir, source_video, transcript, clip)
    clip["verification"] = report
    clip["status"] = "verified" if report["passed"] else "failed"
    clip["updatedAt"] = datetime.utcnow().isoformat() + "Z"
    save_job(job)

    job = load_job(job_id)
    job["status"] = "completed" if report["passed"] else "failed"
    job["progress"] = {
        "stage": "completed" if report["passed"] else "failed",
        "message": f"Re-export finished for {clip['title']}." if report["passed"] else f"Re-export failed verification for {clip['title']}.",
        "percent": 100,
    }
    save_job(job)


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit(
            "Usage: python worker/reexport_clip.py <job_id> <clip_id> <trim_start_seconds> <trim_end_seconds> <subtitle_preset>"
        )

    main(sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5])
