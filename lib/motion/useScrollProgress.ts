"use client";

import { useLenis } from "lenis/react";
import { useMotionValue, useSpring } from "framer-motion";
import { useEffect } from "react";

export function useScrollProgress() {
  const progress = useMotionValue(0);
  const smooth = useSpring(progress, { stiffness: 120, damping: 28, mass: 0.4 });

  useLenis(({ progress: p }) => {
    progress.set(p);
  });

  useEffect(() => {
    const onScroll = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      progress.set(max > 0 ? window.scrollY / max : 0);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [progress]);

  return smooth;
}
