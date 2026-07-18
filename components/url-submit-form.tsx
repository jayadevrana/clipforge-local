"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { ArrowRight, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const IS_HOSTED_PREVIEW =
  process.env.NEXT_PUBLIC_VERCEL_ENV === "preview" || process.env.NEXT_PUBLIC_VERCEL_ENV === "production";

export function UrlSubmitForm() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    startTransition(async () => {
      const response = await fetch("/api/jobs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      const payload = (await response.json()) as { error?: string; id?: string };

      if (!response.ok || !payload.id) {
        setError(payload.error ?? "Unable to start the job.");
        return;
      }

      router.push(`/jobs/${payload.id}`);
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row">
        <Input
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="Paste a public YouTube link"
          className="h-14 flex-1 text-base"
        />
        <Button size="lg" className="min-w-[220px]" disabled={isPending}>
          {isPending ? "Starting session..." : "Generate Clips"}
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
      <div className="flex items-center gap-2 text-sm text-white/55">
        <Sparkles className="h-4 w-4 text-[#e9c7a3]" />
        {IS_HOSTED_PREVIEW
          ? "This hosted preview showcases the product surface. Private worker environments handle media processing."
          : "Private sessions keep source links and export internals out of the visible interface."}
      </div>
      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
    </form>
  );
}
