from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

from .utils import PROJECT_ROOT


JOBS_ROOT = PROJECT_ROOT / "storage" / "jobs"


def job_dir(job_id: str) -> Path:
    return JOBS_ROOT / job_id


def job_file(job_id: str) -> Path:
    return job_dir(job_id) / "job.json"


def load_job(job_id: str) -> dict[str, Any]:
    return json.loads(job_file(job_id).read_text(encoding="utf-8"))


def save_job(job: dict[str, Any]) -> None:
    path = job_file(job["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(job, indent=2), encoding="utf-8")


def update_job(job_id: str, updater: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    current = load_job(job_id)
    updated = deepcopy(updater(current))
    updated["updatedAt"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    save_job(updated)
    return updated


def set_stage(job_id: str, stage: str, message: str, percent: int) -> dict[str, Any]:
    def _update(job: dict[str, Any]) -> dict[str, Any]:
        job["status"] = stage
        job["progress"] = {
            "stage": stage,
            "message": message,
            "percent": percent,
        }
        logs = job.get("logs", [])
        logs.append(f"[{stage}] {message}")
        job["logs"] = logs[-60:]
        return job

    return update_job(job_id, _update)


def fail_job(job_id: str, reason: str) -> dict[str, Any]:
    def _update(job: dict[str, Any]) -> dict[str, Any]:
        job["status"] = "failed"
        job["progress"] = {
            "stage": "failed",
            "message": reason,
            "percent": 100,
        }
        job["failureReason"] = reason
        logs = job.get("logs", [])
        logs.append(f"[failed] {reason}")
        job["logs"] = logs[-60:]
        return job

    return update_job(job_id, _update)

