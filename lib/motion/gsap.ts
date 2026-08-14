"use client";

import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { easings } from "@/lib/motion/tokens";

let registered = false;

export function ensureGsapPlugins() {
  if (typeof window === "undefined" || registered) return;
  gsap.registerPlugin(ScrollTrigger);
  gsap.defaults({
    ease: easings.outCss,
    duration: 0.9,
  });
  registered = true;
}

export { gsap, ScrollTrigger };

export type ScrollRevealVars = gsap.TweenVars & {
  trigger?: Element | string;
  start?: string;
  end?: string;
  scrub?: boolean | number;
  once?: boolean;
  markers?: boolean;
};

/**
 * Create a from→to tween pinned to ScrollTrigger. Returns a cleanup fn.
 */
export function createScrollTween(
  target: gsap.TweenTarget,
  from: gsap.TweenVars,
  to: ScrollRevealVars,
) {
  ensureGsapPlugins();

  const {
    trigger,
    start = "top 85%",
    end = "bottom 15%",
    scrub,
    once = true,
    markers,
    ...tweenVars
  } = to;

  const triggerEl =
    (trigger as Element | undefined) ??
    (Array.isArray(target) ? (target[0] as Element) : (target as Element));

  const tween = gsap.fromTo(target, from, {
    ...tweenVars,
    scrollTrigger: {
      trigger: triggerEl,
      start,
      end,
      scrub: scrub ?? false,
      once,
      markers,
      toggleActions: once ? "play none none none" : "play reverse play reverse",
    },
  });

  return () => {
    tween.scrollTrigger?.kill();
    tween.kill();
  };
}

export function refreshScrollTrigger() {
  if (typeof window === "undefined") return;
  ensureGsapPlugins();
  ScrollTrigger.refresh();
}
