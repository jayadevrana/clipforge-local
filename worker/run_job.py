from __future__ import annotations

import sys
from datetime import datetime

from modules.clip_detector import detect_clips
from modules.export_pipeline import export_clip
from modules.job_store import fail_job, job_dir, load_job, save_job, set_stage
from modules.output_verifier import verify_clip
from modules.transcript_extractor import extract_transcript
from modules.youtube_ingest import download_video


def main(job_id: str) -> None:
    try:
        job = load_job(job_id)
        current_dir = job_dir(job_id)

        set_stage(job_id, "downloading", "Downloading the YouTube source video locally with yt-dlp.", 12)
        metadata, source_video = download_video(current_dir, job["url"])

        job = load_job(job_id)
        job["metadata"] = {
            "title": metadata.get("title"),
            "channel": metadata.get("channel") or metadata.get("uploader"),
            "thumbnail": metadata.get("thumbnail"),
            "duration": metadata.get("duration"),
            "uploader": metadata.get("uploader"),
            "webpageUrl": metadata.get("webpage_url"),
        }
        job["sourceVideoPath"] = str(source_video)
        save_job(job)

        set_stage(job_id, "transcribing", "Extracting timed transcript data from the subtitle track or local Whisper fallback.", 26)
        transcript = extract_transcript(current_dir, job["url"], source_video)

        job = load_job(job_id)
        job["transcriptPath"] = str(current_dir / "source" / "transcript.json")
        job["transcriptPreview"] = transcript["preview"]
        save_job(job)

        set_stage(job_id, "analyzing", "Scoring transcript windows to find strong standalone short-form moments.", 40)
        clips = detect_clips(transcript)

        now = datetime.utcnow().isoformat() + "Z"
        job = load_job(job_id)
        job["clips"] = [
            {
                **clip,
                "status": "pending",
                "createdAt": now,
                "updatedAt": now,
            }
            for clip in clips
        ]
        save_job(job)

        verified_count = 0
        for index in range(len(job["clips"])):
            job = load_job(job_id)
            clip = job["clips"][index]
            set_stage(
                job_id,
                "clipping",
                f"Preparing clip {index + 1} of {len(job['clips'])}: {clip['title']}",
                min(60, 44 + index * 4),
            )
            job = load_job(job_id)
            clip = job["clips"][index]
            clip["status"] = "exporting"
            clip["updatedAt"] = datetime.utcnow().isoformat() + "Z"
            save_job(job)

            set_stage(
                job_id,
                "subtitling",
                f"Generating safe subtitle overlays and layout-aware caption placement for {clip['title']}.",
                min(68, 50 + index * 4),
            )
            job = load_job(job_id)
            clip = job["clips"][index]
            set_stage(
                job_id,
                "exporting",
                f"Rendering vertical export {index + 1} of {len(job['clips'])}.",
                min(82, 58 + index * 6),
            )
            job = load_job(job_id)
            clip = job["clips"][index]
            export_clip(current_dir, source_video, transcript, clip)
            save_job(job)

            set_stage(
                job_id,
                "verifying",
                f"Verifying output {index + 1} of {len(job['clips'])}.",
                min(92, 62 + index * 6),
            )
            job = load_job(job_id)
            clip = job["clips"][index]
            report = verify_clip(current_dir, source_video, transcript, clip)
            clip["verification"] = report
            clip["status"] = "verified" if report["passed"] else "failed"
            clip["updatedAt"] = datetime.utcnow().isoformat() + "Z"
            if report["passed"]:
                verified_count += 1
            save_job(job)

        if verified_count == 0:
            raise RuntimeError("The pipeline finished, but no clips passed automated verification.")

        job = load_job(job_id)
        job["status"] = "completed"
        job["progress"] = {
            "stage": "completed",
            "message": f"Completed with {verified_count} verified clip(s).",
            "percent": 100,
        }
        save_job(job)
    except Exception as exc:
        fail_job(job_id, str(exc))
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python worker/run_job.py <job_id>")
    main(sys.argv[1])
