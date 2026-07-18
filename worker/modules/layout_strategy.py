from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import cv2  # type: ignore
import numpy as np

from .utils import clean_text, run_command, write_json


FINANCE_TERMS = {
    "trading",
    "indicator",
    "chart",
    "market",
    "price",
    "ema",
    "oscillator",
    "candle",
    "oversold",
    "overbought",
    "strategy",
}


def _extract_frame(video_path: Path, timestamp: float, output_path: Path) -> None:
    run_command(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-update",
            "1",
            str(output_path),
        ]
    )


def _ocr_boxes(image_path: Path) -> list[dict]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tsv") as tmp_file:
        tsv_path = Path(tmp_file.name)
    try:
        run_command(
            [
                "tesseract",
                str(image_path),
                str(tsv_path.with_suffix("")),
                "--psm",
                "11",
                "tsv",
            ]
        )
        rows = list(csv.DictReader(tsv_path.read_text(encoding="utf-8").splitlines(), delimiter="\t"))
    finally:
        if tsv_path.exists():
            tsv_path.unlink()

    boxes: list[dict] = []
    for row in rows:
        text = clean_text(row.get("text", ""))
        try:
            conf = float(row.get("conf", "-1"))
        except Exception:
            conf = -1
        if not text or conf < 35:
            continue
        left = int(row["left"])
        top = int(row["top"])
        width = int(row["width"])
        height = int(row["height"])
        boxes.append({"x": left, "y": top, "w": width, "h": height, "text": text, "conf": conf})
    return boxes


def _detect_faces(image_path: Path) -> list[dict]:
    image = cv2.imread(str(image_path))
    if image is None:
        return []
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    classifier = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    detections = classifier.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=5, minSize=(36, 36))
    return [{"x": int(x), "y": int(y), "w": int(w), "h": int(h)} for (x, y, w, h) in detections]


def _saliency_center_x(image_path: Path) -> float:
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return 0.5
    edges = cv2.Canny(image, 60, 180)
    weights = edges.astype(np.float32)
    if weights.sum() <= 0:
        return 0.5
    x_coords = np.tile(np.arange(weights.shape[1], dtype=np.float32), (weights.shape[0], 1))
    return float((x_coords * weights).sum() / weights.sum() / weights.shape[1])


def _merge_boxes(boxes: list[dict], width: int, height: int) -> list[dict]:
    merged: list[dict] = []
    for box in boxes:
        padded = {
            "x": max(0, box["x"] - 8),
            "y": max(0, box["y"] - 8),
            "w": min(width, box["x"] + box["w"] + 8) - max(0, box["x"] - 8),
            "h": min(height, box["y"] + box["h"] + 8) - max(0, box["y"] - 8),
            "text": box["text"],
            "conf": box["conf"],
        }
        merged.append(padded)
    return merged


def _even(value: float) -> int:
    rounded = int(round(value))
    if rounded % 2:
        rounded += 1
    return max(2, rounded)


def analyze_layout(job_dir: Path, source_video: Path, clip: dict, transcript: dict) -> dict:
    sample_times = [
        round(clip["start"] + clip["duration"] * 0.18, 3),
        round(clip["start"] + clip["duration"] * 0.5, 3),
        round(clip["start"] + clip["duration"] * 0.82, 3),
    ]
    sample_dir = job_dir / "tmp" / clip["id"] / "layout"
    sample_dir.mkdir(parents=True, exist_ok=True)

    transcript_text = " ".join(
        cue["text"]
        for cue in transcript["cues"]
        if cue["end"] >= clip["start"] and cue["start"] <= clip["end"]
    ).lower()

    aggregated_boxes: list[dict] = []
    faces: list[dict] = []
    saliency_points: list[float] = []
    source_width = 640
    source_height = 360

    for index, timestamp in enumerate(sample_times):
        frame_path = sample_dir / f"frame-{index}.png"
        _extract_frame(source_video, timestamp, frame_path)
        frame = cv2.imread(str(frame_path))
        if frame is None:
            continue
        source_height, source_width = frame.shape[:2]
        aggregated_boxes.extend(_merge_boxes(_ocr_boxes(frame_path), source_width, source_height))
        faces.extend(_detect_faces(frame_path))
        saliency_points.append(_saliency_center_x(frame_path))

    text_span_left = min((box["x"] for box in aggregated_boxes), default=source_width * 0.4)
    text_span_right = max((box["x"] + box["w"] for box in aggregated_boxes), default=source_width * 0.6)
    text_span_ratio = max(0.0, (text_span_right - text_span_left) / max(source_width, 1))
    edge_text = any(box["x"] < source_width * 0.12 or (box["x"] + box["w"]) > source_width * 0.88 for box in aggregated_boxes)
    top_text = any(box["y"] < source_height * 0.18 for box in aggregated_boxes)
    text_heavy = len(aggregated_boxes) >= 6 or text_span_ratio >= 0.54
    finance_heavy = any(term in transcript_text for term in FINANCE_TERMS)

    face_center_ratio = (
        sum((face["x"] + face["w"] / 2) / source_width for face in faces) / len(faces)
        if faces
        else (sum(saliency_points) / len(saliency_points) if saliency_points else 0.5)
    )

    crop_width = max(1, int(round(source_height * (9 / 16))))
    crop_x = int(round(face_center_ratio * source_width - crop_width / 2))
    crop_x = max(0, min(source_width - crop_width, crop_x))

    crop_safe = True
    for box in aggregated_boxes:
        if box["x"] < crop_x + 10 or (box["x"] + box["w"]) > crop_x + crop_width - 10:
            crop_safe = False
            break

    mode = "full_frame_fit"
    notes: list[str] = []
    if finance_heavy or text_heavy or edge_text or top_text:
        mode = "full_frame_fit"
        notes.append("Protected OCR text reaches the edges or the clip is finance/text heavy, so the full frame stays visible.")
    elif faces and crop_safe:
        mode = "intelligent_crop"
        notes.append("A face is detectable and protected text stays inside a safe crop window.")
    elif faces:
        mode = "hybrid"
        notes.append("A subject is present, but protected text makes a pure crop risky, so the clip uses a hybrid portrait composition.")
    else:
        mode = "full_frame_fit"
        notes.append("No stable face lock was found, so the export preserves the full frame on a portrait canvas.")

    if mode == "intelligent_crop":
        frame_width = 720
        frame_height = 1280
        frame_x = 0
        frame_y = 0
        title_candidates = [56, 98, 148]
        subtitle_candidates = [964, 850, 730]
    elif mode == "hybrid":
        frame_width = 680
        frame_height = _even(source_height * (frame_width / source_width))
        frame_x = (720 - frame_width) // 2
        frame_y = 176
        title_candidates = [52, 84, 118]
        subtitle_candidates = [986, 1080, 870]
    else:
        frame_width = 720
        frame_height = _even(source_height * (frame_width / source_width))
        frame_x = 0
        frame_y = 178
        title_candidates = [50, 84, 118]
        subtitle_candidates = [988, 1080, 870]

    layout = {
        "mode": mode,
        "notes": notes,
        "sourceWidth": source_width,
        "sourceHeight": source_height,
        "cropX": crop_x,
        "cropWidth": crop_width,
        "faceCount": len(faces),
        "textHeavy": text_heavy,
        "financeHeavy": finance_heavy,
        "edgeText": edge_text,
        "topText": top_text,
        "textSpanRatio": round(text_span_ratio, 4),
        "subjectCenterRatio": round(face_center_ratio, 4),
        "protectedBoxes": aggregated_boxes,
        "contentFrame": {
            "x": frame_x,
            "y": frame_y,
            "width": frame_width,
            "height": frame_height,
        },
        "titleCandidates": title_candidates,
        "subtitleCandidates": subtitle_candidates,
    }

    write_json(sample_dir / "layout-analysis.json", layout)
    return layout


def project_box_to_output(box: dict, layout: dict) -> dict | None:
    source_width = layout["sourceWidth"]
    source_height = layout["sourceHeight"]

    if layout["mode"] == "intelligent_crop":
        crop_x = layout["cropX"]
        crop_width = layout["cropWidth"]
        if box["x"] < crop_x or box["x"] + box["w"] > crop_x + crop_width:
            return None
        scale_x = 720 / crop_width
        scale_y = 1280 / source_height
        return {
            "x": int(round((box["x"] - crop_x) * scale_x)),
            "y": int(round(box["y"] * scale_y)),
            "w": int(round(box["w"] * scale_x)),
            "h": int(round(box["h"] * scale_y)),
        }

    frame = layout["contentFrame"]
    scale_x = frame["width"] / source_width
    scale_y = frame["height"] / source_height
    return {
        "x": int(round(frame["x"] + box["x"] * scale_x)),
        "y": int(round(frame["y"] + box["y"] * scale_y)),
        "w": int(round(box["w"] * scale_x)),
        "h": int(round(box["h"] * scale_y)),
    }


def _choose_overlay_y(layout: dict, candidates: list[int], overlay_height: int, overlay_width: int) -> int:
    projected_boxes = [project_box_to_output(box, layout) for box in layout["protectedBoxes"]]
    projected_boxes = [box for box in projected_boxes if box is not None]

    best_y = candidates[0]
    best_overlap = float("inf")
    overlay_x = int((720 - overlay_width) / 2)
    for candidate_y in candidates:
        overlap = 0
        for box in projected_boxes:
            vertical_overlap = max(0, min(candidate_y + overlay_height, box["y"] + box["h"]) - max(candidate_y, box["y"]))
            horizontal_overlap = max(
                0,
                min(overlay_x + overlay_width, box["x"] + box["w"]) - max(overlay_x, box["x"]),
            )
            overlap += vertical_overlap * horizontal_overlap
        if overlap < best_overlap:
            best_overlap = overlap
            best_y = candidate_y

    return int(best_y)


def choose_title_y(layout: dict, title_height: int = 120) -> int:
    return _choose_overlay_y(layout, layout["titleCandidates"], title_height, 720)


def choose_subtitle_y(layout: dict, subtitle_height: int = 210) -> int:
    return _choose_overlay_y(layout, layout["subtitleCandidates"], subtitle_height, 720)


def important_text_preserved(layout: dict) -> bool:
    if layout["mode"] != "intelligent_crop":
        return True

    for box in layout["protectedBoxes"]:
        projected = project_box_to_output(box, layout)
        if projected is None:
            return False
    return True
