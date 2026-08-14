"use client";

import {
  ensureGsapPlugins,
  gsap,
  ScrollTrigger,
} from "@/lib/motion/gsap";
import { distances, durations, easings } from "@/lib/motion/tokens";
import {
  useIsMobileViewport,
  usePrefersReducedMotion,
} from "@/lib/motion/usePrefersReducedMotion";
import { memo, useEffect, useRef, type ReactNode } from "react";

export type ScrollRevealProps = {
  children: ReactNode;
  className?: string;
  delay?: number;
  duration?: number;
  direction?: "up" | "down" | "left" | "right" | "none";
  distance?: number;
  start?: string;
  once?: boolean;
  /** Optional scrubbed reveal for long sections */
  scrub?: boolean | number;
};

function fromVars(
  direction: NonNullable<ScrollRevealProps["direction"]>,
  distance: number,
) {
  switch (direction) {
    case "down":
      return { autoAlpha: 0, y: -distance };
    case "left":
      return { autoAlpha: 0, x: distance };
    case "right":
      return { autoAlpha: 0, x: -distance };
    case "none":
      return { autoAlpha: 0 };
    case "up":
    default:
      return { autoAlpha: 0, y: distance };
  }
}

function ScrollRevealBase({
  children,
  className,
  delay = 0,
  duration = durations.scroll,
  direction = "up",
  distance,
  start = "top 88%",
  once = true,
  scrub = false,
}: ScrollRevealProps) {
  const reduceMotion = usePrefersReducedMotion();
  const isMobile = useIsMobileViewport();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (reduceMotion || !ref.current) return;

    ensureGsapPlugins();
    const el = ref.current;
    const dist = distance ?? (isMobile ? distances.sm : distances.md);

    gsap.set(el, fromVars(direction, dist));

    const tween = gsap.to(el, {
      autoAlpha: 1,
      x: 0,
      y: 0,
      duration: scrub ? undefined : duration,
      delay: scrub ? 0 : delay,
      ease: easings.outCss,
      scrollTrigger: {
        trigger: el,
        start,
        end: scrub ? "top 40%" : undefined,
        scrub: scrub || false,
        once: scrub ? false : once,
        toggleActions: once ? "play none none none" : "play reverse play reverse",
        invalidateOnRefresh: true,
      },
    });

    return () => {
      tween.scrollTrigger?.kill();
      tween.kill();
    };
  }, [delay, direction, distance, duration, isMobile, once, reduceMotion, scrub, start]);

  useEffect(() => {
    if (reduceMotion) return;
    const id = requestAnimationFrame(() => ScrollTrigger.refresh());
    return () => cancelAnimationFrame(id);
  }, [reduceMotion]);

  return (
    <div ref={ref} className={className} data-scroll-reveal="">
      {children}
    </div>
  );
}

export const ScrollReveal = memo(ScrollRevealBase);
