import { cn } from "@/lib/utils";

export function Badge({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-[rgba(255,248,238,0.12)] bg-[rgba(255,248,238,0.05)] px-3 py-1 text-xs font-medium text-white/76",
        className,
      )}
    >
      {children}
    </span>
  );
}
