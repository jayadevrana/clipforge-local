"use client";

import { useState, useTransition } from "react";
import { Download, RefreshCcw, Scissors } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { ClipRecord, SubtitlePreset } from "@/lib/types";
import { formatSeconds, SUBTITLE_PRESETS } from "@/lib/utils";

export function ClipCard({
  jobId,
  clip,
  onReexported,
}: {
  jobId: string;
  clip: ClipRecord;
  onReexported: () => void;
}) {
  const [trimStartSeconds, setTrimStartSeconds] = useState("0");
  const [trimEndSeconds, setTrimEndSeconds] = useState("0");
  const [subtitlePreset, setSubtitlePreset] = useState<SubtitlePreset>(clip.subtitlePreset);
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleReexport() {
    setMessage(null);
    startTransition(async () => {
      const response = await fetch(`/api/jobs/${jobId}/clips/${clip.id}/reexport`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          trimStartSeconds: Number(trimStartSeconds || 0),
          trimEndSeconds: Number(trimEndSeconds || 0),
          subtitlePreset,
        }),
      });

      const payload = (await response.json()) as { error?: string };

      if (!response.ok) {
        setMessage(payload.error ?? "Re-export failed.");
        return;
      }

      setMessage("Re-export queued. The job panel will refresh automatically.");
      onReexported();
    });
  }

  return (
    <Card className="overflow-hidden">
      <div className="space-y-4">
        <div className="overflow-hidden rounded-[20px] border border-white/10 bg-black">
          <video
            className="aspect-[9/16] w-full object-cover"
            controls
            preload="metadata"
            src={`/api/jobs/${jobId}/clips/${clip.id}/video`}
          />
        </div>

        <div className="space-y-3">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-white">{clip.title}</h3>
              <p className="text-sm text-white/55">
                {formatSeconds(clip.start)} - {formatSeconds(clip.end)} · {formatSeconds(clip.duration)}
              </p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <Badge className="border-emerald-300/30 bg-emerald-300/10 text-emerald-50">
                {clip.score}/100
              </Badge>
              {clip.layoutMode ? <Badge>{clip.layoutMode.replaceAll("_", " ")}</Badge> : null}
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {clip.reasonTags.map((reason) => (
              <Badge key={reason}>{reason}</Badge>
            ))}
          </div>

          {clip.layoutNotes?.length ? (
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-white/62">
              <div className="font-medium text-white">Composition</div>
              <ul className="mt-2 space-y-1">
                {clip.layoutNotes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {clip.boundaryNotes?.length ? (
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-white/62">
              <div className="font-medium text-white">Boundary tuning</div>
              <ul className="mt-2 space-y-1">
                {clip.boundaryNotes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="space-y-2 text-sm text-white/60">
              Trim start
              <Input
                type="number"
                step="0.25"
                min="0"
                value={trimStartSeconds}
                onChange={(event) => setTrimStartSeconds(event.target.value)}
              />
            </label>
            <label className="space-y-2 text-sm text-white/60">
              Trim end
              <Input
                type="number"
                step="0.25"
                min="0"
                value={trimEndSeconds}
                onChange={(event) => setTrimEndSeconds(event.target.value)}
              />
            </label>
          </div>

          <label className="space-y-2 text-sm text-white/60">
            Subtitle preset
            <select
              value={subtitlePreset}
              onChange={(event) => setSubtitlePreset(event.target.value as SubtitlePreset)}
              className="h-12 w-full rounded-2xl border border-white/10 bg-white/6 px-4 text-sm text-white outline-none"
            >
              {SUBTITLE_PRESETS.map((preset) => (
                <option key={preset.value} value={preset.value} className="bg-zinc-950">
                  {preset.label}
                </option>
              ))}
            </select>
          </label>

          <div className="grid gap-3 sm:grid-cols-2">
            <Button variant="secondary" onClick={handleReexport} disabled={isPending}>
              <Scissors className="mr-2 h-4 w-4" />
              {isPending ? "Re-exporting..." : "Re-export Clip"}
            </Button>
            <a href={`/api/jobs/${jobId}/clips/${clip.id}/video?download=1`} download>
              <Button variant="ghost" className="w-full border border-white/10 bg-transparent">
                <Download className="mr-2 h-4 w-4" />
                Download
              </Button>
            </a>
          </div>

          {clip.verification ? (
            <div className="rounded-2xl border border-white/10 bg-black/25 p-4 text-sm text-white/70">
              <div className="flex items-center justify-between gap-4">
                <div className="font-medium text-white">
                  Verification: {clip.verification.passed ? "Passed" : "Failed"}
                </div>
                <Badge
                  className={
                    clip.verification.passed
                      ? "border-emerald-300/30 bg-emerald-300/10 text-emerald-50"
                      : "border-rose-300/30 bg-rose-300/10 text-rose-50"
                  }
                >
                  {clip.verification.width}x{clip.verification.height}
                </Badge>
              </div>
              <p className="mt-2 text-white/55">
                Audio similarity:{" "}
                {clip.verification.audioSimilarity ? clip.verification.audioSimilarity.toFixed(3) : "n/a"} ·
                Subtitle diff:{" "}
                {clip.verification.subtitleDiffScore ? clip.verification.subtitleDiffScore.toFixed(2) : "n/a"}
              </p>
              <ul className="mt-3 space-y-1 text-white/55">
                {clip.verification.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-white/10 p-4 text-sm text-white/45">
              Verification pending.
            </div>
          )}

          {message ? (
            <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/4 p-3 text-sm text-white/62">
              <RefreshCcw className="h-4 w-4" />
              {message}
            </div>
          ) : null}
        </div>
      </div>
    </Card>
  );
}
