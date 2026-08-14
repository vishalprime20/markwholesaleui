"use client";

import { type ReactNode } from "react";

export type SectionChapterProps = {
  id: string;
  index: string;
  label: string;
  children: ReactNode;
  className?: string;
};

export function SectionChapter({
  id,
  index,
  label,
  children,
  className = "",
}: SectionChapterProps) {
  return (
    <section id={id} className={`relative scroll-mt-16 pt-8 pb-16 sm:scroll-mt-[4.5rem] sm:pt-10 sm:pb-20 ${className}`}>
      <div
        className="pointer-events-none absolute inset-x-0 top-0 z-[1] h-px bg-gradient-to-r from-transparent via-brand-bright/45 to-transparent"
        aria-hidden
      />
      <div className="pointer-events-none absolute inset-x-0 top-0 z-[1] h-28 steel-grid opacity-[0.09]" aria-hidden />

      <div className="pointer-events-none absolute inset-y-0 left-0 z-20 hidden xl:block">
        <div className="sticky top-28 px-6 2xl:px-8">
          <p className="font-display text-[11px] font-semibold tracking-[0.22em] text-white/35 uppercase">
            {index} / {label}
          </p>
        </div>
      </div>

      {children}
    </section>
  );
}
