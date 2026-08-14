"use client";

import { ParallaxElement, SectionChapter, StaggerChildren } from "@/components/motion";
import { SectionHeading } from "@/components/Reveal";
import { galleryImages } from "@/lib/content";
import { MediaImage as Image } from "@/components/MediaImage";

export function GallerySection() {
  return (
    <SectionChapter id="gallery" index="06" label="Gallery">
      <div className="absolute inset-0 metal-sheen opacity-50" />
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading eyebrow="Visuals" title="Gallery" align="center" />

        <StaggerChildren
          className="mt-12 columns-1 gap-3 sm:columns-2 lg:columns-3"
          itemClassName="mb-3 break-inside-avoid overflow-hidden border border-line"
        >
          {galleryImages.map((src, i) => {
            const isLarge = i % 3 === 0;
            return (
              <div key={src} className="relative aspect-[4/3] overflow-hidden">
                {isLarge ? (
                  <ParallaxElement
                    speed={18}
                    className="absolute inset-x-0 -top-[10%] h-[120%] w-full will-change-transform"
                  >
                    <div className="relative h-full w-full">
                      <Image
                        src={src}
                        alt={`Mark Wholesale gallery ${i + 1}`}
                        fill
                        className="object-cover transition duration-700 hover:scale-105"
                        sizes="(max-width:1024px) 50vw, 33vw"
                      />
                    </div>
                  </ParallaxElement>
                ) : (
                  <Image
                    src={src}
                    alt={`Mark Wholesale gallery ${i + 1}`}
                    fill
                    className="object-cover transition duration-700 hover:scale-105"
                    sizes="(max-width:1024px) 50vw, 33vw"
                  />
                )}
              </div>
            );
          })}
        </StaggerChildren>
      </div>
    </SectionChapter>
  );
}
