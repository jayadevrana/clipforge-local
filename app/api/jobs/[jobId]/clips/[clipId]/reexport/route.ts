import { NextResponse } from "next/server";

import { reexportClip } from "@/lib/jobs";
import { readJob } from "@/lib/storage";
import type { SubtitlePreset } from "@/lib/types";

export const runtime = "nodejs";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ jobId: string; clipId: string }> },
) {
  try {
    const { jobId, clipId } = await params;
    const payload = (await request.json()) as {
      trimStartSeconds?: number;
      trimEndSeconds?: number;
      subtitlePreset?: SubtitlePreset;
    };

    const job = await readJob(jobId);
    const clip = job.clips.find((item) => item.id === clipId);

    if (!clip) {
      return NextResponse.json({ error: "Clip not found." }, { status: 404 });
    }

    await reexportClip(jobId, clipId, {
      trimStartSeconds: Math.max(0, payload.trimStartSeconds ?? 0),
      trimEndSeconds: Math.max(0, payload.trimEndSeconds ?? 0),
      subtitlePreset: payload.subtitlePreset ?? clip.subtitlePreset,
    });

    return NextResponse.json({ ok: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to queue re-export.";
    const status = message.includes("hosted preview") ? 503 : 500;
    return NextResponse.json(
      { error: message },
      { status },
    );
  }
}
