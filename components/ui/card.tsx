import { cn } from "@/lib/utils";

export function Card({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "rounded-[32px] border border-[rgba(255,248,238,0.1)] bg-[linear-gradient(180deg,rgba(255,248,238,0.07),rgba(255,248,238,0.03))] p-5 shadow-[0_24px_80px_rgba(0,0,0,0.28)] backdrop-blur-xl",
        className,
      )}
    >
      {children}
    </div>
  );
}
