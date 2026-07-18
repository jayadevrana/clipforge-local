"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-12 w-full rounded-[24px] border border-[rgba(255,248,238,0.12)] bg-[rgba(255,248,238,0.04)] px-5 text-sm text-white outline-none transition placeholder:text-white/35 focus:border-[#e9c7a3]/70 focus:bg-[rgba(255,248,238,0.07)]",
        className,
      )}
      {...props}
    />
  );
}
