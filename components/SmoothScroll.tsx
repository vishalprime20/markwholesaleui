"use client";

import { ScrollTriggerProvider } from "@/components/motion/ScrollTriggerProvider";
import { usePrefersReducedMotion } from "@/lib/motion/usePrefersReducedMotion";
import { ReactLenis } from "lenis/react";
import type { ReactNode } from "react";

export function SmoothScroll({ children }: { children: ReactNode }) {
  const reduceMotion = usePrefersReducedMotion();

  if (reduceMotion) {
    return <>{children}</>;
  }

  return (
    <ReactLenis root options={{ lerp: 0.08, duration: 1.1, smoothWheel: true }}>
      <ScrollTriggerProvider />
      {children}
    </ReactLenis>
  );
}
