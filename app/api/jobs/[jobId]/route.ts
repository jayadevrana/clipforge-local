import { NextResponse } from "next/server";

import { readJob } from "@/lib/storage";

export const runtime = "nodejs";

export async function GET(_: Request, { params }: { params: Promise<{ jobId: string }> }) {
  try {
    const { jobId } = await params;
    const job = await readJob(jobId);
    return NextResponse.json({
      id: job.id,
      status: job.status,
      progress: job.progress,
      createdAt: job.createdAt,
      updatedAt: job.updatedAt,
      transcriptPreview: job.transcriptPreview,
      metadata: job.metadata
        ? {
            title: job.metadata.title,
            channel: job.metadata.channel,
            duration: job.metadata.duration,
            uploader: job.metadata.uploader,
          }
        : undefined,
      failureReason: job.status === "failed" ? job.failureReason : undefined,
      clips: job.clips.map((clip) => ({
        id: clip.id,
        title: clip.title,
        description: clip.description,
        start: clip.start,
        end: clip.end,
        duration: clip.duration,
        score: clip.score,
        reasonTags: clip.reasonTags,
        subtitlePreset: clip.subtitlePreset,
        status: clip.status,
        notes: clip.notes,
        boundaryNotes: clip.boundaryNotes,
        layoutMode: clip.layoutMode,
        layoutNotes: clip.layoutNotes,
        subtitleY: clip.subtitleY,
        titleY: clip.titleY,
        ocrProtectedBoxCount: clip.ocrProtectedBoxCount,
        verification: clip.verification,
        createdAt: clip.createdAt,
        updatedAt: clip.updatedAt,
      })),
    });
  } catch {
    return NextResponse.json({ error: "Job not found." }, { status: 404 });
  }
}
