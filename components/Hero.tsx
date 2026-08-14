"use client";

import { HeroBackground } from "@/components/HeroBackground";
import { LOGO_WHITE } from "@/components/LogoIntro";
import { MagneticLink } from "@/components/motion";
import { hero, inventoryProducts } from "@/lib/content";
import { useAnchorClick } from "@/lib/motion/useSmoothScrollTo";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { MediaImage as Image } from "@/components/MediaImage";
import { useLayoutEffect, useRef, useState } from "react";

type Product = (typeof inventoryProducts)[number];

type HeroProps = {
  /** False while transparent intro plays — brand logo stays hidden */
  introComplete?: boolean;
};

export function Hero({ introComplete = true }: HeroProps) {
  const reduceMotion = useReducedMotion();
  const onAnchor = useAnchorClick();
  const [active, setActive] = useState<Product | null>(null);
  const preview = active;
  const logoWrapRef = useRef<HTMLDivElement>(null);
  const [logoFrom, setLogoFrom] = useState<{ x: number; y: number; scale: number } | null>(null);
  const [logoPhase, setLogoPhase] = useState<"hidden" | "from" | "to">("hidden");

  useLayoutEffect(() => {
    if (!introComplete) {
      setLogoPhase("hidden");
      setLogoFrom(null);
      return;
    }

    if (reduceMotion) {
      setLogoPhase("to");
      setLogoFrom({ x: 0, y: 0, scale: 1 });
      return;
    }

    const el = logoWrapRef.current;
    if (!el) return;

    const rect = el.getBoundingClientRect();
    const x = window.innerWidth / 2 - (rect.left + rect.width / 2);
    const y = window.innerHeight / 2 - (rect.top + rect.height / 2);
    setLogoFrom({ x, y, scale: 1.12 });
    setLogoPhase("from");

    let raf2 = 0;
    const raf1 = requestAnimationFrame(() => {
      raf2 = requestAnimationFrame(() => setLogoPhase("to"));
    });

    return () => {
      cancelAnimationFrame(raf1);
      cancelAnimationFrame(raf2);
    };
  }, [introComplete, reduceMotion]);

  const showCopy = introComplete;

  return (
    <section id="home" className="relative min-h-[100svh] scroll-mt-20 overflow-x-hidden">
      <HeroBackground />

      {/* Main hero copy — brand first */}
      <div className="relative z-10 mx-auto flex min-h-[100svh] max-w-7xl flex-col justify-end px-4 pb-[11.5rem] pt-28 sm:px-6 sm:pb-[12.5rem] lg:px-8 lg:pb-52">
        <div className="grid items-end gap-8 lg:grid-cols-[1.15fr_0.85fr]">
          <div>
            <motion.div
              ref={logoWrapRef}
              className="origin-center"
              initial={false}
              animate={
                logoPhase === "hidden"
                  ? { opacity: 0, x: 0, y: 0, scale: 1 }
                  : logoPhase === "from" && logoFrom
                    ? { opacity: 1, x: logoFrom.x, y: logoFrom.y, scale: logoFrom.scale }
                    : { opacity: 1, x: 0, y: 0, scale: 1 }
              }
              transition={
                logoPhase === "to"
                  ? { duration: 0.95, ease: [0.22, 1, 0.36, 1] }
                  : { duration: 0 }
              }
              style={{ visibility: logoPhase === "hidden" ? "hidden" : "visible" }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={LOGO_WHITE}
                alt="Mark Wholesale Inc."
                className="h-auto w-[min(88vw,420px)] sm:w-[min(70vw,520px)]"
                draggable={false}
              />
            </motion.div>

            <motion.h1
              className="mt-6 max-w-xl font-display text-2xl font-semibold tracking-tight text-white sm:text-3xl md:text-4xl"
              initial={false}
              animate={
                showCopy
                  ? { opacity: 1, y: 0 }
                  : { opacity: 0, y: reduceMotion ? 0 : 20 }
              }
              transition={{ duration: 0.75, delay: showCopy ? 0.35 : 0, ease: [0.22, 1, 0.36, 1] }}
            >
              {hero.headline}
            </motion.h1>

            <motion.p
              className="mt-3 max-w-md text-base text-white/70 sm:text-lg"
              initial={false}
              animate={
                showCopy
                  ? { opacity: 1, y: 0 }
                  : { opacity: 0, y: reduceMotion ? 0 : 16 }
              }
              transition={{ duration: 0.7, delay: showCopy ? 0.45 : 0 }}
            >
              {hero.subhead}
            </motion.p>

            <motion.div
              className="mt-7 flex flex-wrap gap-3"
              initial={false}
              animate={
                showCopy
                  ? { opacity: 1, y: 0 }
                  : { opacity: 0, y: reduceMotion ? 0 : 14 }
              }
              transition={{ duration: 0.65, delay: showCopy ? 0.55 : 0 }}
            >
              <MagneticLink
                href={hero.ctaPrimary.href}
                onClick={onAnchor}
                className="inline-flex items-center justify-center bg-brand-bright px-6 py-3 text-sm font-semibold tracking-wide text-steel-900 transition hover:bg-[#4db0df]"
              >
                {hero.ctaPrimary.label}
              </MagneticLink>
              <MagneticLink
                href={hero.ctaSecondary.href}
                onClick={onAnchor}
                className="inline-flex items-center justify-center border border-white/25 bg-white/5 px-6 py-3 text-sm font-semibold tracking-wide text-white backdrop-blur-sm transition hover:border-brand-bright/60 hover:bg-white/10"
              >
                {hero.ctaSecondary.label}
              </MagneticLink>
            </motion.div>
          </div>

          {/* Product preview — appears on hover */}
          <div className="pointer-events-none relative hidden lg:block">
            <AnimatePresence mode="wait">
              {preview ? (
                <motion.div
                  key={preview.name}
                  initial={reduceMotion ? false : { opacity: 0, x: 20, filter: "blur(6px)" }}
                  animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
                  exit={reduceMotion ? undefined : { opacity: 0, x: 10, filter: "blur(4px)" }}
                  transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  className="ml-auto w-full max-w-[220px]"
                >
                  <div className="relative overflow-hidden border-l-2 border-brand-bright bg-steel-900/55 p-3 backdrop-blur-xl">
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_30%,rgba(51,153,204,0.18),transparent_60%)]" />
                    <p className="relative text-[10px] font-semibold tracking-[0.24em] text-brand-bright uppercase">
                      Inventory
                    </p>
                    <p className="relative mt-1 font-display text-lg font-semibold text-white">
                      {preview.name}
                    </p>
                    <div className="relative mt-2 aspect-square w-full max-w-[180px]">
                      <Image
                        src={preview.image}
                        alt={preview.name}
                        fill
                        className="object-contain drop-shadow-[0_12px_24px_rgba(0,0,0,0.5)]"
                        sizes="180px"
                        priority
                      />
                    </div>
                  </div>
                </motion.div>
              ) : null}
            </AnimatePresence>
          </div>
        </div>

        {/* Mobile preview */}
        <div className="pointer-events-none mt-6 lg:hidden">
          <AnimatePresence mode="wait">
            {preview ? (
              <motion.div
                key={`m-${preview.name}`}
                initial={reduceMotion ? false : { opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={reduceMotion ? undefined : { opacity: 0, y: 8 }}
                className="flex items-center gap-4 border-l-2 border-brand-bright bg-steel-900/60 p-3 backdrop-blur-xl"
              >
                <div className="relative h-20 w-20 shrink-0">
                  <Image src={preview.image} alt={preview.name} fill className="object-contain" sizes="80px" />
                </div>
                <div>
                  <p className="text-[10px] font-semibold tracking-[0.24em] text-brand-bright uppercase">
                    Inventory
                  </p>
                  <p className="font-display text-xl font-semibold text-white">{preview.name}</p>
                </div>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>
      </div>

      {/* Modern product dock */}
      <div className="absolute inset-x-0 bottom-0 z-20">
        <div className="mx-auto max-w-[1500px] px-3 pb-4 sm:px-5 sm:pb-6">
          <motion.div
            initial={false}
            animate={
              showCopy
                ? { opacity: 1, y: 0 }
                : { opacity: 0, y: reduceMotion ? 0 : 24 }
            }
            transition={{ duration: 0.7, delay: showCopy ? 0.5 : 0 }}
            className="overflow-hidden rounded-2xl border border-white/10 bg-steel-900/70 shadow-[0_-8px_40px_rgba(0,0,0,0.35)] backdrop-blur-2xl"
            onMouseLeave={() => setActive(null)}
          >
            <div className="flex items-center justify-between gap-4 border-b border-white/8 px-4 py-2.5 sm:px-5">
              <p className="text-[10px] font-semibold tracking-[0.3em] text-white/55 uppercase sm:text-xs">
                Products & Inventory
              </p>
              <p className="hidden text-xs text-white/40 sm:block">
                Hover a shape to preview
              </p>
            </div>

            <ul className="flex gap-1.5 overflow-x-auto px-2 py-3 sm:grid sm:grid-cols-6 sm:gap-2 sm:overflow-visible md:grid-cols-12 md:px-3">
              {inventoryProducts.map((product, i) => {
                const isActive = active?.name === product.name;
                return (
                  <li key={product.name} className="min-w-[5.25rem] flex-1 sm:min-w-0">
                    <motion.button
                      type="button"
                      initial={reduceMotion ? false : { opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.4 + i * 0.03, duration: 0.4 }}
                      className={`group relative flex w-full flex-col items-center gap-2 rounded-xl px-1.5 py-2 transition duration-300 ${
                        isActive
                          ? "bg-brand-bright/12 ring-1 ring-brand-bright/45"
                          : "hover:bg-white/5"
                      }`}
                      onMouseEnter={() => setActive(product)}
                      onFocus={() => setActive(product)}
                      onClick={() => setActive(product)}
                      aria-pressed={isActive}
                    >
                      {isActive ? (
                        <span className="absolute inset-x-3 top-0 h-px bg-gradient-to-r from-transparent via-brand-bright to-transparent" />
                      ) : null}
                      <span
                        className={`relative overflow-hidden rounded-lg border transition duration-300 ${
                          isActive
                            ? "scale-105 border-brand-bright/50 shadow-[0_0_18px_rgba(51,153,204,0.35)]"
                            : "border-white/10 group-hover:border-white/25"
                        }`}
                      >
                        <span className="relative block h-12 w-12 bg-black sm:h-14 sm:w-14">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={product.icon}
                            alt=""
                            className="h-full w-full object-cover"
                            draggable={false}
                          />
                        </span>
                      </span>
                      <span
                        className={`text-center text-[9px] font-semibold tracking-[0.06em] uppercase sm:text-[10px] ${
                          isActive ? "text-brand-bright" : "text-white/70 group-hover:text-white"
                        }`}
                      >
                        {product.name}
                      </span>
                    </motion.button>
                  </li>
                );
              })}
            </ul>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
