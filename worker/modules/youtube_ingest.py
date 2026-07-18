from __future__ import annotations

import json
from pathlib import Path

from .utils import python_yt_dlp_args, run_command


def download_video(job_dir: Path, url: str) -> tuple[dict, Path]:
    source_dir = job_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = source_dir / "metadata.json"
    output_template = source_dir / "input.%(ext)s"
    existing_candidates = sorted(source_dir.glob("input.*"))
    if metadata_path.exists() and existing_candidates:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        return metadata, existing_candidates[0]

    metadata_raw = run_command(
        python_yt_dlp_args() + ["--dump-single-json", "--no-playlist", url],
        capture_output=True,
    )
    metadata = json.loads(metadata_raw)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    source_video = source_dir / "input.mp4"

    try:
        run_command(
            python_yt_dlp_args()
            + [
                "--no-playlist",
                "-f",
                "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/b[ext=mp4]/b",
                "--merge-output-format",
                "mp4",
                "-o",
                str(output_template),
                url,
            ]
        )
        if not source_video.exists():
            candidates = sorted(source_dir.glob("input.*"))
            if candidates:
                source_video = candidates[0]
    except Exception:
        from pytubefix import YouTube  # type: ignore

        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()
        if stream is None:
            raise RuntimeError("Both yt-dlp and pytubefix failed to resolve a downloadable MP4 stream.")
        stream.download(output_path=str(source_dir), filename="input.mp4")

    return metadata, source_video
