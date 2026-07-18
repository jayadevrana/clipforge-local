import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

import type { JobStage, SubtitlePreset } from "@/lib/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatSeconds(totalSeconds: number) {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;

  if (hours > 0) {
    return [hours, minutes, remainder]
      .map((value, index) => (index === 0 ? `${value}` : `${value}`.padStart(2, "0")))
      .join(":");
  }

  return [minutes, remainder].map((value) => `${value}`.padStart(2, "0")).join(":");
}

export const STAGE_ORDER: JobStage[] = [
  "queued",
  "downloading",
  "transcribing",
  "analyzing",
  "clipping",
  "subtitling",
  "exporting",
  "verifying",
  "completed",
];

export function formatStageLabel(stage: JobStage) {
  return stage.replace("-", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export function isTerminalStage(stage: JobStage) {
  return stage === "completed" || stage === "failed";
}

export const SUBTITLE_PRESETS: Array<{ value: SubtitlePreset; label: string }> = [
  { value: "clean-minimal", label: "Clean Minimal" },
  { value: "bold-viral", label: "Bold Viral" },
  { value: "creator-neon", label: "Creator Neon" },
];

export function formatDate(value?: string) {
  if (!value) return "Unknown";

  try {
    return new Intl.DateTimeFormat("en", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}
