"use client";

import { FadeIn, ParallaxElement, PinOnDesktop, SectionChapter, SlideIn } from "@/components/motion";
import { SectionHeading } from "@/components/Reveal";
import { about } from "@/lib/content";
import Image from "next/image";

export function AboutSection() {
  return (
    <SectionChapter id="about" index="02" label="About">
      <div className="absolute inset-0 metal-sheen opacity-80" />
      <div className="relative mx-auto grid max-w-7xl gap-12 px-4 sm:px-6 lg:grid-cols-2 lg:items-start lg:px-8">
        <div>
          <SectionHeading eyebrow="Company" title={about.title} />
          <div className="mt-8 space-y-5 text-sm leading-relaxed text-muted sm:text-base">
            {about.paragraphs.map((p, i) => (
              <FadeIn key={p.slice(0, 32)} delay={0.08 + i * 0.08}>
                <p>{p}</p>
              </FadeIn>
            ))}
          </div>
        </div>
        <SlideIn direction="left" delay={0.12}>
          <PinOnDesktop distance="+=70vh">
            <div className="relative aspect-[4/3] overflow-hidden border border-line">
              <ParallaxElement
                speed={28}
                className="absolute inset-x-0 -top-[12%] h-[124%] w-full will-change-transform"
              >
                <div className="relative h-full w-full">
                  <Image
                    src={about.image}
                    alt="Caisson threadbar cages"
                    fill
                    className="object-cover"
                    sizes="(max-width:1024px) 100vw, 50vw"
                  />
                </div>
              </ParallaxElement>
              <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-steel-900/70 via-transparent to-transparent" />
            </div>
          </PinOnDesktop>
        </SlideIn>
      </div>
    </SectionChapter>
  );
}
