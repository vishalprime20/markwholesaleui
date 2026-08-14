"use client";

import { about, completedProjects, featuredProjects, galleryImages, hero, productsDetail, services } from "@/lib/content";
import { LOGO_WHITE } from "@/components/LogoIntro";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";
import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";

const titleClass =
  "font-display text-[clamp(1.65rem,3.8vh,2.5rem)] font-semibold tracking-tight text-white";
const bodyClass = "text-[clamp(0.7rem,1.42vh,0.88rem)] leading-[1.45] text-white/72";
const stackClass = "mt-[clamp(0.55rem,1.5vh,1rem)] space-y-[clamp(0.4rem,1.1vh,0.75rem)]";

function Eyebrow({ children }: { children: string }) {
  return (
    <p className="mb-2 text-[11px] font-semibold tracking-[0.28em] text-brand-bright uppercase">{children}</p>
  );
}

function Title({ children }: { children: string }) {
  return <h2 className={titleClass}>{children}</h2>;
}

function HomeCopy({
  onViewProducts,
  onContact,
}: {
  onViewProducts?: () => void;
  onContact?: () => void;
}) {
  return (
    <div className="flex max-h-full flex-col overflow-hidden">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={LOGO_WHITE}
        alt="Mark Wholesale Inc."
        className="h-auto w-[min(72vw,300px)]"
        draggable={false}
      />
      <h1 className={`${titleClass} mt-[clamp(0.7rem,1.8vh,1.15rem)] max-w-xl`}>{hero.headline}</h1>
      <p className={`mt-[clamp(0.4rem,1vh,0.65rem)] max-w-lg ${bodyClass}`}>{hero.subhead}</p>
      <div className="mt-[clamp(0.85rem,2vh,1.35rem)] flex flex-wrap gap-2.5">
        <button
          type="button"
          onClick={onViewProducts}
          className="inline-flex items-center justify-center bg-brand-bright px-5 py-2.5 text-xs font-semibold tracking-wide text-steel-900 transition hover:bg-[#4db0df] sm:text-sm"
        >
          {hero.ctaPrimary.label}
        </button>
        <button
          type="button"
          onClick={onContact}
          className="inline-flex items-center justify-center border border-white/25 bg-white/5 px-5 py-2.5 text-xs font-semibold tracking-wide text-white backdrop-blur-sm transition hover:border-brand-bright/60 hover:bg-white/10 sm:text-sm"
        >
          {hero.ctaSecondary.label}
        </button>
      </div>
    </div>
  );
}

function AboutCopy() {
  return (
    <div className="flex max-h-full flex-col overflow-hidden">
      <Eyebrow>Company</Eyebrow>
      <Title>{about.title}</Title>
      <div className={`${stackClass} ${bodyClass}`}>
        {about.paragraphs.map((p) => (
          <p key={p.slice(0, 32)}>{p}</p>
        ))}
      </div>
    </div>
  );
}

function ServicesCopy() {
  const logos = [...services.marketLogos, ...services.marketLogos];
  return (
    <div className="flex max-h-full flex-col overflow-hidden">
      <Eyebrow>Trading</Eyebrow>
      <Title>{services.title}</Title>
      <p className={`mt-[clamp(0.45rem,1.2vh,0.75rem)] font-medium text-white/90 ${bodyClass}`}>
        {services.lead}
      </p>
      <p className={`mt-[clamp(0.4rem,1.1vh,0.7rem)] ${bodyClass}`}>{services.body}</p>
      <p className="mt-[clamp(0.85rem,2vh,1.35rem)] mb-2 text-[11px] font-semibold tracking-[0.28em] text-brand-bright uppercase">
        {services.platformTitle}
      </p>
      <div className="overflow-hidden border border-white/15 bg-black/20 py-3">
        <div className="marquee-track flex w-max gap-8 px-3">
          {logos.map((logo, i) => (
            <div
              key={`${logo.name}-${i}`}
              className="relative flex h-8 w-20 shrink-0 items-center justify-center sm:h-10 sm:w-28"
            >
              <Image src={logo.src} alt={logo.name} fill className="object-contain" sizes="112px" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ProductsCopy() {
  return (
    <div className="flex max-h-full flex-col overflow-hidden">
      <Eyebrow>Steel</Eyebrow>
      <Title>{productsDetail.title}</Title>
      <p className="mt-[clamp(0.4rem,1.1vh,0.7rem)] text-[11px] font-semibold tracking-wide text-brand-bright uppercase">
        {productsDetail.featuring}
      </p>
      <div className={`${stackClass} ${bodyClass}`}>
        <p>{productsDetail.hotCarbon}</p>
        <p>{productsDetail.coated}</p>
      </div>
      <div className="mt-[clamp(0.6rem,1.5vh,1rem)] flex flex-wrap gap-1.5">
        {productsDetail.steelProducts.map((name) => (
          <div
            key={name}
            className="border border-white/20 bg-white/5 px-2 py-1 text-[11px] text-white/90 sm:text-xs"
          >
            {name}
          </div>
        ))}
      </div>
      <p className="mt-[clamp(0.75rem,1.8vh,1.15rem)] mb-2 text-[11px] font-semibold tracking-[0.28em] text-white/50 uppercase">
        Mill Partners
      </p>
      <div className="grid grid-cols-4 gap-1.5 sm:grid-cols-5">
        {productsDetail.suppliers.map((s) => (
          <div
            key={s.name}
            className="relative flex h-9 items-center justify-center border border-white/15 bg-white px-1 sm:h-11"
          >
            <Image src={s.src} alt={s.name} width={80} height={28} className="max-h-5 w-auto object-contain sm:max-h-6" />
          </div>
        ))}
      </div>
    </div>
  );
}

const foundationLabels: Record<string, string> = {
  CAISSON_PLAIN_PIPE: "Caisson Pipe",
  HP_Pile_Beams: "H-Pile Beams",
  Soldier_Pile: "Soldier Pile",
  "Drilling_Tie-Backs_MicroPiles": "Tie-Backs / Micropiles",
  MicroPile_Pipe: "Micropile Pipe",
  Support_Of_Excavation: "Support of Excavation",
  Deep_Foundation_Wrakers: "Wrakers",
  Threaded_bar2: "Threaded Bar",
};

function foundationLabel(src: string) {
  const file = src.split("/").pop()?.replace(/\.(jpe?g|png|webp)$/i, "") ?? "";
  return foundationLabels[file] ?? file.replaceAll("_", " ");
}

function FoundationCopy() {
  return (
    <div className="flex max-h-full flex-col overflow-hidden">
      <Eyebrow>Specialty</Eyebrow>
      <Title>{productsDetail.deepFoundationTitle}</Title>
      <p className={`mt-[clamp(0.45rem,1.2vh,0.75rem)] ${bodyClass}`}>
        Caisson pipe, H-pile beams, soldier pile, micropiles, tie-backs, support of excavation, wrakers, and
        threaded bar for Northeast deep-foundation work.
      </p>
      <div className="mt-[clamp(0.55rem,1.5vh,1rem)] grid grid-cols-4 gap-1.5">
        {productsDetail.deepFoundationImages.map((src) => (
          <figure key={src} className="overflow-hidden border border-white/15 bg-black/25">
            <div className="relative aspect-[4/3]">
              <Image src={src} alt={foundationLabel(src)} fill className="object-cover" sizes="160px" />
            </div>
            <figcaption className="px-1.5 py-1 text-[10px] leading-tight font-medium tracking-wide text-white/80 uppercase sm:text-[11px]">
              {foundationLabel(src)}
            </figcaption>
          </figure>
        ))}
      </div>
    </div>
  );
}

function ProjectsCopy() {
  return (
    <div className="flex max-h-full flex-col overflow-hidden">
      <Eyebrow>Portfolio</Eyebrow>
      <Title>Projects</Title>
      <div className="mt-[clamp(0.45rem,1.2vh,0.75rem)] grid grid-cols-3 gap-1.5">
        {featuredProjects.map((project) => (
          <article key={project.title} className="overflow-hidden border border-white/15 bg-black/25">
            <div className="relative aspect-[16/10]">
              <Image src={project.image} alt={project.title} fill className="object-cover" sizes="180px" />
            </div>
            <p className="px-1.5 py-1 font-display text-[10px] leading-tight font-semibold text-white sm:text-[11px]">
              {project.title}
            </p>
          </article>
        ))}
      </div>
      <h3 className="font-display mt-[clamp(0.55rem,1.4vh,0.9rem)] text-[clamp(0.95rem,2.2vh,1.2rem)] font-semibold text-white">
        Project’s Completed
      </h3>
      <ul className="mt-1.5 grid grid-cols-2 gap-x-3 gap-y-0.5">
        {completedProjects.map((item) => (
          <li
            key={item}
            className="truncate border-l-2 border-brand-bright/60 bg-black/20 px-2 py-0.5 text-[10px] leading-snug text-white/70 sm:text-[11px]"
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function GalleryCopy() {
  const total = galleryImages.length;
  const [index, setIndex] = useState(0);
  const [dir, setDir] = useState(1);
  const pausedRef = useRef(false);
  const touchX = useRef(0);
  const wheelLock = useRef(false);

  const go = useCallback(
    (next: number, direction: number) => {
      setDir(direction);
      setIndex((next + total) % total);
    },
    [total],
  );

  useEffect(() => {
    const id = window.setInterval(() => {
      if (pausedRef.current) return;
      go(index + 1, 1);
    }, 4200);
    return () => window.clearInterval(id);
  }, [go, index]);

  return (
    <div
      className="flex max-h-full w-full flex-col overflow-hidden"
      data-gallery-slider
      onMouseEnter={() => {
        pausedRef.current = true;
      }}
      onMouseLeave={() => {
        pausedRef.current = false;
      }}
      onWheel={(event) => {
        event.stopPropagation();
        if (wheelLock.current) return;
        if (Math.abs(event.deltaY) < 20 && Math.abs(event.deltaX) < 20) return;
        const delta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
        wheelLock.current = true;
        window.setTimeout(() => {
          wheelLock.current = false;
        }, 480);
        go(index + (delta > 0 ? 1 : -1), delta > 0 ? 1 : -1);
      }}
    >
      <Eyebrow>Visuals</Eyebrow>
      <Title>Gallery</Title>

      <div
        className="relative mt-[clamp(0.45rem,1.2vh,0.75rem)] aspect-[16/10] w-full overflow-hidden border border-white/15 bg-black/30"
        onTouchStart={(event) => {
          touchX.current = event.touches[0]?.clientX ?? 0;
        }}
        onTouchEnd={(event) => {
          const endX = event.changedTouches[0]?.clientX ?? touchX.current;
          const dx = touchX.current - endX;
          if (Math.abs(dx) < 40) return;
          go(index + (dx > 0 ? 1 : -1), dx > 0 ? 1 : -1);
        }}
      >
        <AnimatePresence initial={false} custom={dir} mode="wait">
          <motion.div
            key={galleryImages[index]}
            custom={dir}
            initial={{ x: dir > 0 ? "18%" : "-18%", opacity: 0 }}
            animate={{ x: "0%", opacity: 1 }}
            exit={{ x: dir > 0 ? "-18%" : "18%", opacity: 0 }}
            transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
            className="absolute inset-0"
          >
            <Image
              src={galleryImages[index]}
              alt={`Mark Wholesale gallery ${index + 1}`}
              fill
              className="object-cover"
              sizes="680px"
              priority={index === 0}
            />
          </motion.div>
        </AnimatePresence>

        <button
          type="button"
          aria-label="Previous image"
          className="absolute top-1/2 left-2 z-10 flex h-8 w-8 -translate-y-1/2 items-center justify-center border border-white/25 bg-black/45 text-white backdrop-blur-sm transition hover:bg-black/70"
          onClick={() => go(index - 1, -1)}
        >
          <ChevronLeft size={18} strokeWidth={2.25} />
        </button>
        <button
          type="button"
          aria-label="Next image"
          className="absolute top-1/2 right-2 z-10 flex h-8 w-8 -translate-y-1/2 items-center justify-center border border-white/25 bg-black/45 text-white backdrop-blur-sm transition hover:bg-black/70"
          onClick={() => go(index + 1, 1)}
        >
          <ChevronRight size={18} strokeWidth={2.25} />
        </button>

        <p className="absolute right-2 bottom-2 z-10 bg-black/50 px-2 py-0.5 text-[10px] font-medium tracking-wide text-white/80">
          {index + 1} / {total}
        </p>
      </div>

      <div className="mt-2 flex gap-1.5 overflow-x-auto pb-0.5">
        {galleryImages.map((src, i) => (
          <button
            key={src}
            type="button"
            aria-label={`Show gallery image ${i + 1}`}
            aria-current={i === index}
            onClick={() => go(i, i > index ? 1 : -1)}
            className={`relative h-11 w-[4.4rem] shrink-0 overflow-hidden border transition sm:h-12 sm:w-20 ${
              i === index ? "border-brand-bright opacity-100" : "border-white/15 opacity-55 hover:opacity-90"
            }`}
          >
            <Image src={src} alt="" fill className="object-cover" sizes="80px" />
          </button>
        ))}
      </div>
    </div>
  );
}

export function ToonHubSlideCopy({
  sectionId,
  onViewProducts,
  onContact,
}: {
  sectionId: string;
  onViewProducts?: () => void;
  onContact?: () => void;
}) {
  switch (sectionId) {
    case "home":
      return <HomeCopy onViewProducts={onViewProducts} onContact={onContact} />;
    case "about":
      return <AboutCopy />;
    case "services":
      return <ServicesCopy />;
    case "products":
      return <ProductsCopy />;
    case "foundation":
      return <FoundationCopy />;
    case "projects":
      return <ProjectsCopy />;
    case "gallery":
      return <GalleryCopy />;
    default:
      return null;
  }
}
