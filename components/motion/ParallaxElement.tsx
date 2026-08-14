"use client";

import {
  ensureGsapPlugins,
  gsap,
  ScrollTrigger,
} from "@/lib/motion/gsap";
import { distances } from "@/lib/motion/tokens";
import {
  useIsMobileViewport,
  usePrefersReducedMotion,
} from "@/lib/motion/usePrefersReducedMotion";
import { memo, useEffect, useRef, type ReactNode } from "react";

export type ParallaxElementProps = {
  children: ReactNode;
  className?: string;
  /** Vertical travel in px (auto-capped on mobile) */
  speed?: number;
  /** Scroll range relative to the element */
  start?: string;
  end?: string;
};

function ParallaxElementBase({
  children,
  className,
  speed,
  start = "top bottom",
  end = "bottom top",
}: ParallaxElementProps) {
  const reduceMotion = usePrefersReducedMotion();
  const isMobile = useIsMobileViewport();
  const ref = useRef<HTMLDivElement>(null);

  const travel =
    speed ?? (isMobile ? distances.parallaxMobile : distances.parallaxDesktop);

  useEffect(() => {
    if (reduceMotion || !ref.current) return;

    ensureGsapPlugins();
    const el = ref.current;

    const tween = gsap.fromTo(
      el,
      { y: -travel * 0.35 },
      {
        y: travel * 0.65,
        ease: "none",
        scrollTrigger: {
          trigger: el,
          start,
          end,
          scrub: isMobile ? 0.6 : 0.35,
          invalidateOnRefresh: true,
        },
      },
    );

    return () => {
      tween.scrollTrigger?.kill();
      tween.kill();
    };
  }, [end, isMobile, reduceMotion, start, travel]);

  useEffect(() => {
    if (reduceMotion) return;
    const id = requestAnimationFrame(() => ScrollTrigger.refresh());
    return () => cancelAnimationFrame(id);
  }, [reduceMotion]);

  return (
    <div ref={ref} className={className} data-parallax="">
      {children}
    </div>
  );
}

export const ParallaxElement = memo(ParallaxElementBase);
