"use client";

import {
  ParallaxElement,
  PinOnDesktop,
  ScrollReveal,
  SectionChapter,
  StaggerChildren,
} from "@/components/motion";
import { SectionHeading } from "@/components/Reveal";
import { productsDetail } from "@/lib/content";
import Image from "next/image";

export function ProductsSection() {
  return (
    <SectionChapter id="products" index="04" label="Products">
      <div className="absolute inset-0 metal-sheen opacity-60" />
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading eyebrow="Steel" title={productsDetail.title} />
        <ScrollReveal delay={0.06}>
          <p className="mt-4 text-sm font-semibold tracking-wide text-brand-bright uppercase">
            {productsDetail.featuring}
          </p>
          <p className="mt-4 max-w-4xl text-sm leading-relaxed text-muted sm:text-base">
            {productsDetail.hotCarbon}
          </p>
          <p className="mt-3 max-w-4xl text-sm leading-relaxed text-muted sm:text-base">
            {productsDetail.coated}
          </p>
        </ScrollReveal>

        <StaggerChildren className="mt-10 flex flex-wrap gap-2" staggerDelay={0.04}>
          {productsDetail.steelProducts.map((name) => (
            <div
              key={name}
              className="border border-line bg-steel-700/50 px-3 py-2 text-sm text-foreground/90"
            >
              {name}
            </div>
          ))}
        </StaggerChildren>

        <PinOnDesktop className="mt-14" distance="+=45vh" start="top 18%">
          <p className="mb-6 text-xs font-semibold tracking-[0.28em] text-muted uppercase">
            Mill Partners
          </p>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-5">
            {productsDetail.suppliers.map((s) => (
              <div
                key={s.name}
                className="relative flex h-20 items-center justify-center border border-line bg-white/95 px-3"
              >
                <Image
                  src={s.src}
                  alt={s.name}
                  width={140}
                  height={56}
                  className="max-h-12 w-auto object-contain"
                />
              </div>
            ))}
          </div>

          <div className="mt-16">
            <SectionHeading title={productsDetail.deepFoundationTitle} />
            <div className="mt-8 grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
              {productsDetail.deepFoundationImages.map((src) => (
                <div key={src} className="relative aspect-[4/3] overflow-hidden border border-line">
                  <ParallaxElement
                    speed={20}
                    className="absolute inset-x-0 -top-[10%] h-[120%] w-full will-change-transform"
                  >
                    <div className="relative h-full w-full">
                      <Image
                        src={src}
                        alt="Deep foundation product"
                        fill
                        className="object-cover transition duration-500 hover:scale-105"
                        sizes="(max-width:768px) 50vw, 25vw"
                      />
                    </div>
                  </ParallaxElement>
                </div>
              ))}
            </div>
          </div>
        </PinOnDesktop>
      </div>
    </SectionChapter>
  );
}
