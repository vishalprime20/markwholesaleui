"use client";

import { usePrefersReducedMotion } from "@/lib/motion/usePrefersReducedMotion";
import { useLenis } from "lenis/react";
import { useCallback, type MouseEvent } from "react";

export const NAV_OFFSET = -72;

export const SPY_SECTION_IDS = [
  "home",
  "inventory",
  "about",
  "services",
  "products",
  "projects",
  "gallery",
  "contact",
] as const;

export function useSmoothScrollTo() {
  const lenis = useLenis();
  const reduceMotion = usePrefersReducedMotion();

  return useCallback(
    (href: string) => {
      if (!href.startsWith("#")) return;
      const id = href.slice(1);
      const el = document.getElementById(id);
      if (!el) return;

      if (reduceMotion || !lenis) {
        el.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
        return;
      }

      lenis.scrollTo(el, { offset: NAV_OFFSET, duration: 1.15 });
    },
    [lenis, reduceMotion],
  );
}

export function useAnchorClick(onAfter?: () => void) {
  const scrollTo = useSmoothScrollTo();

  return useCallback(
    (event: MouseEvent<HTMLAnchorElement>) => {
      const href = event.currentTarget.getAttribute("href");
      if (!href?.startsWith("#")) return;
      event.preventDefault();
      scrollTo(href);
      onAfter?.();
    },
    [onAfter, scrollTo],
  );
}
