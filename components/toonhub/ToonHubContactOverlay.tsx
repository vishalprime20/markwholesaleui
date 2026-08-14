"use client";

import { ContactPanel } from "@/components/contact/ContactPanel";
import { contact } from "@/lib/content";
import { ArrowLeft } from "lucide-react";
import { useEffect } from "react";

export function ToonHubContactOverlay({
  open,
  onClose,
  onHome,
}: {
  open: boolean;
  onClose: () => void;
  onHome: () => void;
}) {
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  return (
    <div
      className={`fixed inset-0 z-[80] overflow-hidden bg-steel-900 transition-opacity duration-500 ${
        open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"
      }`}
      aria-hidden={!open}
    >
      <div className="mx-auto flex h-svh max-w-7xl flex-col px-4 py-4 sm:px-6 sm:py-5 lg:px-8">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center gap-2 text-sm font-semibold tracking-wide text-white/80 uppercase transition hover:text-white"
          >
            <ArrowLeft size={18} strokeWidth={2.25} />
            Back
          </button>
          <button
            type="button"
            onClick={onHome}
            className="text-sm font-semibold tracking-[0.18em] text-brand-bright uppercase transition hover:text-white"
          >
            Back to Home
          </button>
        </div>

        <p className="mb-1 text-[11px] font-semibold tracking-[0.28em] text-brand-bright uppercase">
          Get in touch
        </p>
        <h2 className="font-display mb-4 text-[clamp(1.65rem,3.8vh,2.5rem)] font-semibold tracking-tight text-white">
          {contact.title}
        </h2>

        <div className="min-h-0 flex-1">
          <ContactPanel idPrefix="toonhub-" compact />
        </div>
      </div>
    </div>
  );
}
