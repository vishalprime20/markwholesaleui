"use client";

import { ScrollReveal, SectionChapter, SlideIn } from "@/components/motion";
import { SectionHeading } from "@/components/Reveal";
import { services } from "@/lib/content";
import Image from "next/image";

export function ServicesSection() {
  const logos = [...services.marketLogos, ...services.marketLogos];

  return (
    <SectionChapter
      id="services"
      index="03"
      label="Services"
      className="border-y border-line bg-steel-800"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading eyebrow="Trading" title={services.title} />
        <ScrollReveal delay={0.08}>
          <p className="mt-4 max-w-3xl text-lg font-medium text-foreground/90">{services.lead}</p>
          <p className="mt-5 max-w-4xl text-sm leading-relaxed text-muted sm:text-base">{services.body}</p>
        </ScrollReveal>

        <SlideIn delay={0.12} className="mt-14">
          <p className="mb-6 text-xs font-semibold tracking-[0.28em] text-brand-bright uppercase">
            {services.platformTitle}
          </p>
          <div className="overflow-hidden border border-line bg-steel-900/50 py-6">
            <div className="marquee-track flex w-max gap-12 px-6">
              {logos.map((logo, i) => (
                <div
                  key={`${logo.name}-${i}`}
                  className="relative flex h-12 w-28 shrink-0 items-center justify-center opacity-80 grayscale transition hover:opacity-100 hover:grayscale-0 sm:h-14 sm:w-36"
                >
                  <Image
                    src={logo.src}
                    alt={logo.name}
                    fill
                    className="object-contain"
                    sizes="144px"
                  />
                </div>
              ))}
            </div>
          </div>
        </SlideIn>
      </div>
    </SectionChapter>
  );
}
