from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .layout_strategy import choose_subtitle_y, choose_title_y
from .utils import clean_text


PRESETS = {
    "clean-minimal": {
        "font_size": 48,
        "fill": (255, 255, 255, 255),
        "outline": (0, 0, 0, 210),
        "stroke": 3,
        "bg": None,
        "title_fill": (255, 255, 255, 255),
        "title_bg": (5, 12, 18, 220),
    },
    "bold-viral": {
        "font_size": 58,
        "fill": (255, 255, 255, 255),
        "outline": (8, 8, 8, 255),
        "stroke": 4,
        "bg": (58, 214, 134, 185),
        "title_fill": (7, 17, 13, 255),
        "title_bg": (74, 222, 128, 255),
    },
    "creator-neon": {
        "font_size": 54,
        "fill": (241, 247, 255, 255),
        "outline": (12, 6, 18, 255),
        "stroke": 4,
        "bg": (10, 16, 33, 175),
        "title_fill": (255, 255, 255, 255),
        "title_bg": (72, 96, 255, 220),
    },
}

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica.ttc",
]


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_words(words: list[str], max_words_per_line: int = 4) -> str:
    lines = [" ".join(words[index : index + max_words_per_line]) for index in range(0, len(words), max_words_per_line)]
    return "\n".join(lines[:2])


def _split_cue(cue: dict) -> list[dict]:
    words = cue["words"]
    if len(words) <= 5:
        return [cue]

    chunk_size = 5
    chunk_count = math.ceil(len(words) / chunk_size)
    chunk_duration = cue["duration"] / chunk_count
    split_cues = []
    for index in range(chunk_count):
        chunk_words = words[index * chunk_size : (index + 1) * chunk_size]
        start = cue["start"] + index * chunk_duration
        end = min(cue["end"], cue["start"] + (index + 1) * chunk_duration)
        split_cues.append(
            {
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": round(max(0.35, end - start), 3),
                "text": " ".join(chunk_words),
                "words": chunk_words,
            }
        )
    return split_cues


def _render_text_image(text: str, preset_name: str, output_path: Path, title: bool = False) -> None:
    preset = PRESETS[preset_name]
    width, height = (720, 210) if not title else (720, 120)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = _font(28 if title else preset["font_size"])

    content = clean_text(text)
    if preset_name == "bold-viral" and not title:
        content = content.upper()
    if not title:
        content = _wrap_words(content.split())

    bbox = draw.multiline_textbbox((0, 0), content, font=font, stroke_width=preset["stroke"], align="center")
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) / 2
    y = (height - text_height) / 2

    background = preset["title_bg"] if title else preset["bg"]
    if background is not None:
        pad_x = 32 if title else 26
        pad_y = 18 if title else 20
        draw.rounded_rectangle(
            (x - pad_x, y - pad_y, x + text_width + pad_x, y + text_height + pad_y),
            radius=30 if title else 34,
            fill=background,
        )

    fill = preset["title_fill"] if title else preset["fill"]
    draw.multiline_text(
        (x, y),
        content,
        font=font,
        fill=fill,
        stroke_width=preset["stroke"],
        stroke_fill=preset["outline"],
        align="center",
        spacing=6,
    )
    image.save(output_path)


def build_subtitle_assets(job_dir: Path, clip: dict, transcript: dict, preset_name: str, layout: dict) -> dict:
    tmp_dir = job_dir / "tmp" / clip["id"]
    tmp_dir.mkdir(parents=True, exist_ok=True)
    clip_start = clip["start"]
    clip_end = clip["end"]

    overlays: list[dict] = []
    relevant_cues = [
        cue
        for raw_cue in transcript["cues"]
        if raw_cue["end"] >= clip_start and raw_cue["start"] <= clip_end
        for cue in _split_cue(raw_cue)
    ]

    title_path = tmp_dir / "title.png"
    _render_text_image(clip["title"], preset_name, title_path, title=True)
    title_y = choose_title_y(layout)
    overlays.append(
        {
            "path": str(title_path),
            "start": 0.2,
            "end": min(2.6, clip["duration"] * 0.28 + 1.1),
            "y": title_y,
        }
    )

    subtitle_y = choose_subtitle_y(layout)
    for index, cue in enumerate(relevant_cues):
        start = max(0.0, cue["start"] - clip_start)
        end = max(start + 0.35, min(clip["duration"], cue["end"] - clip_start))
        if end <= 0.1 or start >= clip["duration"]:
            continue

        image_path = tmp_dir / f"subtitle-{index:03d}.png"
        _render_text_image(cue["text"], preset_name, image_path)
        overlays.append(
            {
                "path": str(image_path),
                "start": round(start, 3),
                "end": round(end, 3),
                "y": subtitle_y,
            }
        )

    manifest = {
        "preset": preset_name,
        "overlayCount": len(overlays),
        "layoutMode": layout["mode"],
        "titleY": title_y,
        "subtitleY": subtitle_y,
        "overlays": overlays,
    }
    manifest_path = tmp_dir / "manifest.json"
    manifest_path.write_text(__import__("json").dumps(manifest, indent=2), encoding="utf-8")

    return manifest
