import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import type { JobRecord } from "@/lib/types";

export const PROJECT_ROOT = process.cwd();
export const STORAGE_ROOT = path.join(PROJECT_ROOT, "storage");
export const JOBS_ROOT = path.join(STORAGE_ROOT, "jobs");

export function getJobDir(jobId: string) {
  return path.join(JOBS_ROOT, jobId);
}

export function getJobFile(jobId: string) {
  return path.join(getJobDir(jobId), "job.json");
}

export function getClipOutputDir(jobId: string) {
  return path.join(getJobDir(jobId), "exports");
}

export async function ensureStorageLayout(jobId?: string) {
  await mkdir(STORAGE_ROOT, { recursive: true });
  await mkdir(JOBS_ROOT, { recursive: true });

  if (jobId) {
    await mkdir(getJobDir(jobId), { recursive: true });
    await mkdir(path.join(getJobDir(jobId), "source"), { recursive: true });
    await mkdir(path.join(getJobDir(jobId), "tmp"), { recursive: true });
    await mkdir(getClipOutputDir(jobId), { recursive: true });
  }
}

export async function writeJob(job: JobRecord) {
  await ensureStorageLayout(job.id);
  const file = getJobFile(job.id);
  const tempFile = `${file}.tmp`;
  await writeFile(tempFile, JSON.stringify(job, null, 2), "utf8");
  await rename(tempFile, file);
}

export async function readJob(jobId: string) {
  const file = getJobFile(jobId);
  const raw = await readFile(file, "utf8");
  return JSON.parse(raw) as JobRecord;
}

export async function updateJob(jobId: string, updater: (job: JobRecord) => JobRecord) {
  const current = await readJob(jobId);
  const updated = updater(current);
  updated.updatedAt = new Date().toISOString();
  await writeJob(updated);
  return updated;
}

export function readJobSync(jobId: string) {
  const file = getJobFile(jobId);

  if (!existsSync(file)) {
    return null;
  }

  return JSON.parse(readFileSync(file, "utf8")) as JobRecord;
}
