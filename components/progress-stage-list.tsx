import type { JobStage } from "@/lib/types";
import { STAGE_ORDER, cn, formatStageLabel } from "@/lib/utils";

export function ProgressStageList({
  currentStage,
  percent,
}: {
  currentStage: JobStage;
  percent: number;
}) {
  const currentIndex = STAGE_ORDER.indexOf(currentStage);

  return (
    <div className="space-y-4">
      <div className="h-2 overflow-hidden rounded-full bg-white/8">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-300 via-cyan-300 to-lime-200 transition-all duration-500"
          style={{ width: `${Math.min(100, Math.max(percent, 3))}%` }}
        />
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        {STAGE_ORDER.map((stage, index) => {
          const state =
            stage === currentStage
              ? "active"
              : currentIndex >= 0 && index < currentIndex
                ? "done"
                : "idle";

          return (
            <div
              key={stage}
              className={cn(
                "rounded-2xl border px-3 py-2 text-sm transition-colors",
                state === "done" && "border-emerald-300/30 bg-emerald-300/10 text-emerald-100",
                state === "active" && "border-cyan-300/30 bg-cyan-300/10 text-cyan-50",
                state === "idle" && "border-white/8 bg-white/4 text-white/45",
              )}
            >
              {formatStageLabel(stage)}
            </div>
          );
        })}
      </div>
    </div>
  );
}

