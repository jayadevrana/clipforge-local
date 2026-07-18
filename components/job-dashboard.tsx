"use client";

import { useEffect, useMemo, useState } from "react";
import { Film, RefreshCw, ShieldCheck, Video } from "lucide-react";

import { ClipCard } from "@/components/clip-card";
import { ProgressStageList } from "@/components/progress-stage-list";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { JobRecord } from "@/lib/types";
import { formatDate, formatSeconds, isTerminalStage } from "@/lib/utils";

async function loadJob(jobId: string) {
  const response = await fetch(`/api/jobs/${jobId}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Unable to load job.");
  }

  return (await response.json()) as JobRecord;
}

export function JobDashboard({ jobId }: { jobId: string }) {
  const [job, setJob] = useState<JobRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    let timer: number | undefined;
    let stopped = false;

    async function poll() {
      try {
        const nextJob = await loadJob(jobId);
        if (stopped) return;
        setJob(nextJob);
        setError(null);

        if (!isTerminalStage(nextJob.status)) {
          timer = window.setTimeout(poll, 2200);
        }
      } catch (nextError) {
        if (stopped) return;
        setError(nextError instanceof Error ? nextError.message : "Unable to load job.");
        timer = window.setTimeout(poll, 3000);
      }
    }

    void poll();

    return () => {
      stopped = true;
      if (timer) {
        window.clearTimeout(timer);
      }
    };
  }, [jobId, refreshToken]);

  const verifiedClips = useMemo(
    () => job?.clips.filter((clip) => clip.verification?.passed) ?? [],
    [job?.clips],
  );

  if (error && !job) {
    return <div className="text-sm text-rose-300">{error}</div>;
  }

  if (!job) {
    return <div className="text-sm text-white/55">Loading local job state...</div>;
  }

  return (
    <div className="space-y-8">
      <section className="grid gap-6 lg:grid-cols-[1.25fr_0.85fr]">
        <Card className="space-y-5">
          <div className="flex flex-wrap items-center gap-3">
            <Badge className="border-[rgba(233,199,163,0.18)] bg-[rgba(233,199,163,0.08)] text-[#f3deca]">
              Private session
            </Badge>
            <Badge className={job.status === "failed" ? "border-rose-300/30 bg-rose-300/10 text-rose-50" : ""}>
              {job.status}
            </Badge>
          </div>

          <div className="space-y-2">
            <h1 className="max-w-3xl text-3xl font-semibold text-white">
              {job.metadata?.title ?? "Processing the source video"}
            </h1>
            <p className="max-w-2xl text-sm leading-7 text-white/55">
              Link details and storage paths stay hidden from the visible interface while the session is running.
            </p>
          </div>

          <ProgressStageList currentStage={job.progress.stage} percent={job.progress.percent} />

          <div className="rounded-[24px] border border-white/10 bg-black/25 p-5">
            <div className="text-sm font-medium text-white">Current status</div>
            <p className="mt-2 text-sm leading-7 text-white/60">{job.progress.message}</p>
            {job.failureReason ? (
              <p className="mt-3 text-sm text-rose-300">{job.failureReason}</p>
            ) : null}
          </div>
        </Card>

        <Card className="space-y-5">
          <div className="flex items-center gap-3 text-white">
            <Film className="h-5 w-5 text-[#e9c7a3]" />
            Session details
          </div>
          <div className="grid gap-4 text-sm text-white/62">
            <div>
              <div className="text-white/45">Source</div>
              <div className="mt-1 text-white">{job.metadata?.title ?? "Resolving..."}</div>
            </div>
            <div>
              <div className="text-white/45">Channel</div>
              <div className="mt-1 text-white">{job.metadata?.channel ?? "Resolving..."}</div>
            </div>
            <div>
              <div className="text-white/45">Duration</div>
              <div className="mt-1 text-white">
                {job.metadata?.duration ? formatSeconds(job.metadata.duration) : "Resolving..."}
              </div>
            </div>
            <div>
              <div className="text-white/45">Session opened</div>
              <div className="mt-1 text-white">{formatDate(job.createdAt)}</div>
            </div>
            <div>
              <div className="text-white/45">Story preview</div>
              <div className="mt-1 leading-7 text-white/72">{job.transcriptPreview ?? "Waiting for transcript..."}</div>
            </div>
          </div>
        </Card>
      </section>

      <section className="grid gap-5 md:grid-cols-3">
        <Card className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-white/52">
            <Video className="h-4 w-4 text-cyan-300" />
            Generated clips
          </div>
          <div className="text-3xl font-semibold text-white">{job.clips.length}</div>
        </Card>
        <Card className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-white/52">
            <ShieldCheck className="h-4 w-4 text-emerald-300" />
            Verified clips
          </div>
          <div className="text-3xl font-semibold text-white">{verifiedClips.length}</div>
        </Card>
        <Card className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-white/52">
            <RefreshCw className="h-4 w-4 text-lime-300" />
            Updated
          </div>
          <div className="text-3xl font-semibold text-white">{formatDate(job.updatedAt)}</div>
        </Card>
      </section>

      <section className="space-y-4">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold text-white">Verified clips</h2>
            <p className="mt-2 text-sm text-white/55">
              Only clips that passed the automated verification suite are presented here.
            </p>
          </div>
        </div>

        {verifiedClips.length > 0 ? (
          <div className="grid gap-6 xl:grid-cols-2">
            {verifiedClips.map((clip) => (
              <ClipCard
                key={clip.id}
                jobId={jobId}
                clip={clip}
                onReexported={() => {
                  setRefreshToken((value) => value + 1);
                  void loadJob(jobId).then(setJob);
                }}
              />
            ))}
          </div>
        ) : (
          <Card className="text-sm text-white/55">
            {job.status === "failed"
              ? "The job failed before any verified clips were produced."
              : "The worker is still exporting and verifying clips."}
          </Card>
        )}
      </section>
    </div>
  );
}
