"use client";

import { ensureGsapPlugins, ScrollTrigger } from "@/lib/motion/gsap";
import {
  useIsMobileViewport,
  usePrefersReducedMotion,
} from "@/lib/motion/usePrefersReducedMotion";
import { memo, useEffect, useRef, type ReactNode } from "react";

export type PinOnDesktopProps = {
  children: ReactNode;
  className?: string;
  /** Extra scroll distance while pinned */
  distance?: string;
  start?: string;
};

function PinOnDesktopBase({
  children,
  className,
  distance = "+=85%",
  start = "top 112px",
}: PinOnDesktopProps) {
  const reduceMotion = usePrefersReducedMotion();
  const isMobile = useIsMobileViewport();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (reduceMotion || isMobile || !ref.current) return;

    ensureGsapPlugins();
    const trigger = ScrollTrigger.create({
      trigger: ref.current,
      start,
      end: distance,
      pin: true,
      pinSpacing: true,
      invalidateOnRefresh: true,
    });

    const id = requestAnimationFrame(() => ScrollTrigger.refresh());

    return () => {
      cancelAnimationFrame(id);
      trigger.kill();
    };
  }, [distance, isMobile, reduceMotion, start]);

  return (
    <div ref={ref} className={className} data-pin-desktop="">
      {children}
    </div>
  );
}

export const PinOnDesktop = memo(PinOnDesktopBase);
