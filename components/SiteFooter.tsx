"use client";

import { BrandMark } from "@/components/LogoIntro";
import { FadeIn } from "@/components/motion";

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-steel-900 py-10">
      <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-6 px-4 sm:flex-row sm:items-center sm:px-6 lg:px-8">
        <FadeIn>
          <BrandMark className="h-8 sm:h-9" variant="white" />
        </FadeIn>
        <FadeIn delay={0.1} className="flex flex-col gap-1 text-sm text-muted sm:items-end">
          <p>Matels Trading Division</p>
          <a href="/toonhub" className="transition hover:text-brand-bright">
            Demo v2
          </a>
          <p>© {new Date().getFullYear()} Mark Wholesale Inc.</p>
        </FadeIn>
      </div>
    </footer>
  );
}
