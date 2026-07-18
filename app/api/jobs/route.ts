import { NextResponse } from "next/server";

import { createJob } from "@/lib/jobs";

export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as { url?: string };
    const url = payload.url?.trim();

    if (!url) {
      return NextResponse.json({ error: "A YouTube URL is required." }, { status: 400 });
    }

    const job = await createJob(url);
    return NextResponse.json({ id: job.id });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to create the job.";
    const status = message.includes("hosted preview") ? 503 : 500;
    return NextResponse.json(
      { error: message },
      { status },
    );
  }
}
