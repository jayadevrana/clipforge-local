from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_command(args: list[str], cwd: Path | None = None, capture_output: bool = False) -> str:
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=capture_output,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else "Unknown command failure"
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{stderr}")

    return result.stdout if capture_output else ""


def python_yt_dlp_args() -> list[str]:
    return [sys.executable, "-m", "yt_dlp"]


def slugify(value: str, fallback: str = "clip") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:60] or fallback


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def seconds_to_timestamp(value: float) -> str:
    value = max(0.0, value)
    hours = int(value // 3600)
    minutes = int((value % 3600) // 60)
    seconds = int(value % 60)
    milliseconds = int(round((value - int(value)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def seconds_to_ass(value: float) -> str:
    value = max(0.0, value)
    hours = int(value // 3600)
    minutes = int((value % 3600) // 60)
    seconds = int(value % 60)
    centiseconds = int(round((value - int(value)) * 100))
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("&nbsp;", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def escape_ass_text(value: str) -> str:
    return value.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")


def path_for_filter(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace("'", r"\'")
