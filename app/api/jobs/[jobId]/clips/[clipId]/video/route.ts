import { createReadStream, existsSync } from "node:fs";
import path from "node:path";
import { Readable } from "node:stream";

import { readJob } from "@/lib/storage";

export const runtime = "nodejs";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ jobId: string; clipId: string }> },
) {
  const { jobId, clipId } = await params;
  const url = new URL(request.url);
  const shouldDownload = url.searchParams.get("download") === "1";

  try {
    const job = await readJob(jobId);
    const clip = job.clips.find((item) => item.id === clipId);

    if (!clip?.outputPath || !existsSync(clip.outputPath)) {
      return new Response("Clip not found.", { status: 404 });
    }

    const stream = createReadStream(clip.outputPath);
    const filename = path.basename(clip.outputPath);

    return new Response(Readable.toWeb(stream) as ReadableStream, {
      headers: {
        "Content-Type": "video/mp4",
        "Content-Disposition": shouldDownload ? `attachment; filename="${filename}"` : `inline; filename="${filename}"`,
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return new Response("Clip not found.", { status: 404 });
  }
}
