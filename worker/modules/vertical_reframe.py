from __future__ import annotations

def _progress_filter(duration: float) -> str:
    progress_duration = max(duration, 0.5)
    return (
        "drawbox=x=0:y=0:w='720*min(t/"
        f"{progress_duration}"
        ",1)':h=14:color=0x4ade80@0.92:t=fill,format=yuv420p"
    )


def build_base_filter(layout: dict, duration: float) -> tuple[str, str]:
    mode = layout["mode"]
    content = layout["contentFrame"]
    source_width = layout["sourceWidth"]
    source_height = layout["sourceHeight"]
    progress_filter = _progress_filter(duration)

    if mode == "intelligent_crop":
        crop_width = layout["cropWidth"]
        crop_x = layout["cropX"]
        filter_parts = [
            f"[0:v]crop={crop_width}:{source_height}:{crop_x}:0,"
            "scale=720:1280:flags=lanczos,"
            "eq=saturation=1.04:contrast=1.03:brightness=0.01[main]",
            f"[main]{progress_filter}[vbase]",
        ]
        return ";".join(filter_parts), "vbase"

    if mode == "hybrid":
        filter_parts = [
            f"[0:v]crop={layout['cropWidth']}:{source_height}:{layout['cropX']}:0,"
            "scale=720:1280:flags=lanczos,"
            "boxblur=18:6,"
            "eq=brightness=-0.20:saturation=0.55:contrast=1.04[bg]",
            f"[0:v]scale={content['width']}:{content['height']}:flags=lanczos,"
            "eq=saturation=1.06:contrast=1.04[fg]",
            f"[bg][fg]overlay=x={content['x']}:y={content['y']}[main]",
            f"[main]{progress_filter}[vbase]",
        ]
        return ";".join(filter_parts), "vbase"

    filter_parts = [
        "[0:v]scale=720:1280:force_original_aspect_ratio=increase:flags=lanczos,"
        "crop=720:1280,"
        "boxblur=18:6,"
        "eq=brightness=-0.18:saturation=0.55:contrast=1.03[bg]",
        f"[0:v]scale={content['width']}:{content['height']}:flags=lanczos,"
        "eq=saturation=1.06:contrast=1.04[fg]",
        f"[bg][fg]overlay=x={content['x']}:y={content['y']}[main]",
        f"[main]{progress_filter}[vbase]",
    ]
    return ";".join(filter_parts), "vbase"
