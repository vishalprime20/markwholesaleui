"use client";

import { ensureGsapPlugins, ScrollTrigger } from "@/lib/motion/gsap";
import { usePrefersReducedMotion } from "@/lib/motion/usePrefersReducedMotion";
import { useLenis } from "lenis/react";
import { useEffect, type ReactNode } from "react";

/**
 * Keeps GSAP ScrollTrigger in sync with Lenis smooth scroll.
 * Mount inside ReactLenis (see SmoothScroll).
 */
export function ScrollTriggerProvider({ children }: { children?: ReactNode }) {
  const reduceMotion = usePrefersReducedMotion();
  const lenis = useLenis();

  useEffect(() => {
    if (reduceMotion) return;
    ensureGsapPlugins();
  }, [reduceMotion]);

  useEffect(() => {
    if (reduceMotion || !lenis) return;

    ensureGsapPlugins();

    const onScroll = () => ScrollTrigger.update();
    lenis.on("scroll", onScroll);

    const onRefresh = () => lenis.resize();
    ScrollTrigger.addEventListener("refresh", onRefresh);
    ScrollTrigger.refresh();

    return () => {
      lenis.off("scroll", onScroll);
      ScrollTrigger.removeEventListener("refresh", onRefresh);
    };
  }, [lenis, reduceMotion]);

  return children ? <>{children}</> : null;
}
