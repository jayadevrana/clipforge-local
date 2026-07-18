import { spawn } from "node:child_process";
import path from "node:path";

import { ensureStorageLayout, getClipOutputDir, writeJob } from "@/lib/storage";
import type { JobRecord, SubtitlePreset } from "@/lib/types";

const PROJECT_ROOT = process.env.CLIPLINE_PROJECT_ROOT || ".";

function getPythonBin() {
  return process.env.CLIPLINE_PYTHON_BIN || "python3";
}

function assertYouTubeUrl(value: string) {
  try {
    const parsed = new URL(value);
    const allowedHosts = ["youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"];
    return allowedHosts.includes(parsed.hostname);
  } catch {
    return false;
  }
}

function isHostedPreviewMode() {
  return process.env.VERCEL === "1" && process.env.ENABLE_SERVER_PROCESSING !== "1";
}

export async function createJob(url: string) {
  if (!assertYouTubeUrl(url)) {
    throw new Error("Please provide a valid YouTube URL.");
  }

  if (isHostedPreviewMode()) {
    throw new Error("This hosted preview showcases the interface. Media processing stays available in private worker environments.");
  }

  const id = crypto.randomUUID().split("-")[0];
  await ensureStorageLayout(id);

  const now = new Date().toISOString();
  const job: JobRecord = {
    id,
    url,
    status: "queued",
    progress: {
      stage: "queued",
      message: "Job queued for local processing.",
      percent: 2,
    },
    createdAt: now,
    updatedAt: now,
    outputDir: getClipOutputDir(id),
    clips: [],
    logs: [],
  };

  await writeJob(job);
  const python = getPythonBin();
  const scriptPath = path.join(PROJECT_ROOT, "worker", "run_job.py");
  const child = spawn(python, [scriptPath, id], {
    cwd: PROJECT_ROOT,
    detached: true,
    stdio: "ignore",
  });
  child.unref();

  return job;
}

export async function reexportClip(
  jobId: string,
  clipId: string,
  payload: { trimStartSeconds: number; trimEndSeconds: number; subtitlePreset: SubtitlePreset },
) {
  if (isHostedPreviewMode()) {
    throw new Error("Re-export is unavailable in the hosted preview.");
  }

  const python = getPythonBin();
  const scriptPath = path.join(PROJECT_ROOT, "worker", "reexport_clip.py");
  const child = spawn(
    python,
    [
      scriptPath,
      jobId,
      clipId,
      `${payload.trimStartSeconds}`,
      `${payload.trimEndSeconds}`,
      payload.subtitlePreset,
    ],
    {
      cwd: PROJECT_ROOT,
      detached: true,
      stdio: "ignore",
    },
  );
  child.unref();
}
