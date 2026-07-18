import { ArrowUpRight, AudioLines, Captions, Eye, Layers2, ScanSearch, Shield, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { UrlSubmitForm } from "@/components/url-submit-form";

const workflow = [
  {
    label: "Read the frame",
    description: "OCR and protected zones keep titles, labels, charts, and interface text intact before a layout mode is chosen.",
    icon: Eye,
  },
  {
    label: "Shape the story",
    description: "Sentence-aware boundaries add lead-in and tail-out so each export feels self-contained instead of abruptly clipped.",
    icon: Sparkles,
  },
  {
    label: "Finish with restraint",
    description: "Portrait composition, subtitle safety, original audio preservation, and export verification are handled in one pass.",
    icon: Shield,
  },
];

export default function Home() {
  return (
    <main className="grain-overlay relative overflow-hidden">
      <section className="relative mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 pb-18 pt-8 sm:px-10 lg:px-12">
        <header className="flex items-center justify-between py-5">
          <div className="space-y-2">
            <div className="text-[11px] uppercase tracking-[0.34em] text-white/42">Cutline</div>
            <div className="text-sm text-white/55">Private vertical editing for screen-heavy video.</div>
          </div>
          <Badge className="border-[rgba(233,199,163,0.18)] bg-[rgba(233,199,163,0.08)] text-[#f6e6d5]">
            Built for readability first
          </Badge>
        </header>

        <div className="grid flex-1 items-center gap-16 py-10 lg:grid-cols-[1.04fr_0.96fr]">
          <div className="rise-in space-y-10">
            <div className="space-y-5">
              <Badge className="border-[rgba(233,199,163,0.16)] bg-[rgba(233,199,163,0.08)] text-[#f3deca]">
                Text-safe reframing, clean captions, calm finishing
              </Badge>
              <h1
                className="max-w-4xl text-5xl leading-[0.96] tracking-[-0.04em] text-white sm:text-6xl lg:text-7xl"
                style={{ fontFamily: "var(--font-fraunces)" }}
              >
                Vertical edits that keep the frame intact.
              </h1>
              <p className="max-w-2xl text-[17px] leading-8 text-white/62">
                Cutline turns wide, information-dense video into portrait clips that still read clearly. Charts stay
                visible. Headings stay whole. Captions land where they belong.
              </p>
            </div>

            <div className="max-w-2xl rounded-[34px] border border-[rgba(255,248,238,0.1)] bg-[linear-gradient(180deg,rgba(255,248,238,0.09),rgba(255,248,238,0.04))] p-5 shadow-[0_24px_90px_rgba(0,0,0,0.24)] backdrop-blur-2xl sm:p-6">
              <UrlSubmitForm />
            </div>

            <div className="grid gap-4 pt-2 sm:grid-cols-3">
              <div className="border-t border-[rgba(255,248,238,0.12)] pt-4">
                <div className="text-[11px] uppercase tracking-[0.3em] text-white/42">Layout system</div>
                <div className="mt-3 text-2xl font-semibold text-white">Fit, crop, or hybrid</div>
                <p className="mt-2 text-sm leading-7 text-white/52">Each clip picks the least destructive portrait treatment scene by scene.</p>
              </div>
              <div className="border-t border-[rgba(255,248,238,0.12)] pt-4">
                <div className="text-[11px] uppercase tracking-[0.3em] text-white/42">Audio rule</div>
                <div className="mt-3 text-2xl font-semibold text-white">Original speech only</div>
                <p className="mt-2 text-sm leading-7 text-white/52">No dubbing, no rewritten script, no synthetic replacement voice.</p>
              </div>
              <div className="border-t border-[rgba(255,248,238,0.12)] pt-4">
                <div className="text-[11px] uppercase tracking-[0.3em] text-white/42">Verification</div>
                <div className="mt-3 text-2xl font-semibold text-white">Readable and checked</div>
                <p className="mt-2 text-sm leading-7 text-white/52">Exports are tested for vertical format, audio presence, subtitles, and boundary quality.</p>
              </div>
            </div>
          </div>

          <div className="relative min-h-[680px]">
            <div className="absolute right-[6%] top-0 h-56 w-56 rounded-full bg-[rgba(233,199,163,0.16)] blur-3xl" />
            <div className="absolute bottom-[8%] left-[10%] h-52 w-52 rounded-full bg-[rgba(123,84,55,0.2)] blur-3xl" />

            <div className="float-slow absolute left-0 top-[10%] h-[440px] w-[210px] rounded-[38px] border border-[rgba(255,248,238,0.14)] bg-[linear-gradient(180deg,rgba(24,21,18,0.96),rgba(15,12,10,0.92))] p-4 shadow-[0_28px_90px_rgba(0,0,0,0.34)]">
              <div className="h-full rounded-[28px] border border-[rgba(255,248,238,0.08)] bg-[linear-gradient(180deg,#1d1714_0%,#11100f_100%)] p-4">
                <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.24em] text-white/38">
                  <span>Frame-safe</span>
                  <span>9:16</span>
                </div>
                <div className="mt-5 h-40 rounded-[24px] bg-[linear-gradient(180deg,rgba(233,199,163,0.22),rgba(74,51,35,0.12))]" />
                <div className="mt-5 space-y-3">
                  <div className="h-2 rounded-full bg-[rgba(255,248,238,0.1)]" />
                  <div className="h-2 w-4/5 rounded-full bg-[rgba(255,248,238,0.08)]" />
                  <div className="h-28 rounded-[22px] border border-[rgba(255,248,238,0.08)] bg-[radial-gradient(circle_at_60%_12%,rgba(233,199,163,0.26),transparent_38%),#171310]" />
                </div>
                <div className="mt-6 rounded-full bg-[#f4e8d9] px-4 py-3 text-center text-sm font-semibold text-[#191310]">
                  Chart preserved
                </div>
              </div>
            </div>

            <div className="absolute left-[24%] top-[2%] h-[520px] w-[248px] rounded-[42px] border border-[rgba(255,248,238,0.16)] bg-[linear-gradient(180deg,rgba(35,28,24,0.96),rgba(17,14,12,0.96))] p-4 shadow-[0_40px_120px_rgba(0,0,0,0.38)]">
              <div className="h-full rounded-[30px] border border-[rgba(255,248,238,0.08)] bg-[linear-gradient(180deg,#221b17_0%,#13100e_100%)] p-4">
                <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-white/38">
                  <ScanSearch className="h-3.5 w-3.5 text-[#e9c7a3]" />
                  Protected zones
                </div>
                <div className="mt-4 h-52 rounded-[24px] bg-[linear-gradient(180deg,rgba(255,248,238,0.08),rgba(255,248,238,0.01)),radial-gradient(circle_at_50%_20%,rgba(233,199,163,0.25),transparent_34%),#14100d]" />
                <div className="mt-4 rounded-[24px] border border-[rgba(255,248,238,0.08)] bg-[rgba(255,248,238,0.03)] p-4">
                  <div className="text-lg font-semibold text-white">Choose the quietest layout.</div>
                  <p className="mt-2 text-sm leading-7 text-white/56">
                    The system keeps edge text intact before it ever thinks about a portrait crop.
                  </p>
                </div>
                <div className="mt-4 flex items-center gap-2 text-sm text-white/58">
                  <Layers2 className="h-4 w-4 text-[#e9c7a3]" />
                  Full-frame fit when readability wins
                </div>
              </div>
            </div>

            <div className="absolute right-0 top-[16%] w-[280px] rounded-[36px] border border-[rgba(255,248,238,0.1)] bg-[linear-gradient(180deg,rgba(255,248,238,0.08),rgba(255,248,238,0.03))] p-6 shadow-[0_28px_100px_rgba(0,0,0,0.3)] backdrop-blur-xl">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium text-white">Why it feels finished</div>
                <ArrowUpRight className="h-4 w-4 text-[#e9c7a3]" />
              </div>
              <div className="mt-6 space-y-5">
                {workflow.map((feature) => (
                  <div key={feature.label} className="border-t border-[rgba(255,248,238,0.08)] pt-4 first:border-t-0 first:pt-0">
                    <div className="flex items-center gap-3 text-white">
                      <feature.icon className="h-4.5 w-4.5 text-[#e9c7a3]" />
                      <span className="font-medium">{feature.label}</span>
                    </div>
                    <p className="mt-2 text-sm leading-7 text-white/56">{feature.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <section className="grid gap-10 border-t border-[rgba(255,248,238,0.1)] py-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <div className="text-[11px] uppercase tracking-[0.32em] text-white/42">Designed for difficult footage</div>
            <h2
              className="mt-4 max-w-xl text-4xl leading-tight text-white"
              style={{ fontFamily: "var(--font-fraunces)" }}
            >
              Built for charts, slides, dashboards, and text-led screens that usually break in portrait.
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            <div>
              <Captions className="h-5 w-5 text-[#e9c7a3]" />
              <div className="mt-4 text-lg font-semibold text-white">Captions with manners</div>
              <p className="mt-2 text-sm leading-7 text-white/55">Subtitle placement respects the source frame instead of piling over labels and UI.</p>
            </div>
            <div>
              <AudioLines className="h-5 w-5 text-[#e9c7a3]" />
              <div className="mt-4 text-lg font-semibold text-white">Audio stays untouched</div>
              <p className="mt-2 text-sm leading-7 text-white/55">The spoken track is preserved exactly, with no synthetic dubbing or rewritten delivery.</p>
            </div>
            <div>
              <Shield className="h-5 w-5 text-[#e9c7a3]" />
              <div className="mt-4 text-lg font-semibold text-white">Verification before delivery</div>
              <p className="mt-2 text-sm leading-7 text-white/55">Only exports that pass format, readability, and boundary checks make it through as finished clips.</p>
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}
