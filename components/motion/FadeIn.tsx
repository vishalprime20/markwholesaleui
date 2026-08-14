"use client";

import { durations, easings, viewport } from "@/lib/motion/tokens";
import { usePrefersReducedMotion } from "@/lib/motion/usePrefersReducedMotion";
import { motion } from "framer-motion";
import { memo, type ReactNode } from "react";

export type FadeInProps = {
  children: ReactNode;
  className?: string;
  delay?: number;
  duration?: number;
  /** Fade on mount instead of while-in-view */
  immediate?: boolean;
};

function FadeInBase({
  children,
  className,
  delay = 0,
  duration = durations.base,
  immediate = false,
}: FadeInProps) {
  const reduceMotion = usePrefersReducedMotion();

  if (reduceMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0 }}
      {...(immediate
        ? { animate: { opacity: 1 } }
        : {
            whileInView: { opacity: 1 },
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

export const FadeIn = memo(FadeInBase);
