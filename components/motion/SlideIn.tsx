"use client";

import { distances, durations, easings, viewport } from "@/lib/motion/tokens";
import {
  useIsMobileViewport,
  usePrefersReducedMotion,
} from "@/lib/motion/usePrefersReducedMotion";
import { motion } from "framer-motion";
import { memo, type ReactNode } from "react";

export type SlideInProps = {
  children: ReactNode;
  className?: string;
  delay?: number;
  duration?: number;
  direction?: "up" | "down" | "left" | "right";
  distance?: number;
  immediate?: boolean;
};

function offsetFor(
  direction: NonNullable<SlideInProps["direction"]>,
  distance: number,
) {
  switch (direction) {
    case "down":
      return { x: 0, y: -distance };
    case "left":
      return { x: distance, y: 0 };
    case "right":
      return { x: -distance, y: 0 };
    case "up":
    default:
      return { x: 0, y: distance };
  }
}

function SlideInBase({
  children,
  className,
  delay = 0,
  duration = durations.slow,
  direction = "up",
  distance,
  immediate = false,
}: SlideInProps) {
  const reduceMotion = usePrefersReducedMotion();
  const isMobile = useIsMobileViewport();

  if (reduceMotion) {
    return <div className={className}>{children}</div>;
  }

  const dist = distance ?? (isMobile ? distances.sm : distances.md);
  const from = offsetFor(direction, dist);

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, ...from }}
      {...(immediate
        ? { animate: { opacity: 1, x: 0, y: 0 } }
        : {
            whileInView: { opacity: 1, x: 0, y: 0 },
            viewport: {
              once: viewport.once,
              amount: viewport.amount,
              margin: viewport.margin,
            },
          })}
      transition={{ duration, delay, ease: easings.out }}
    >
      {children}
    </motion.div>
  );
}

export const SlideIn = memo(SlideInBase);
