"use client";

import { RevealText, SlideIn } from "@/components/motion";
import { distances, durations, easings, viewport } from "@/lib/motion/tokens";
import { usePrefersReducedMotion } from "@/lib/motion/usePrefersReducedMotion";
import { motion } from "framer-motion";
import type { ReactNode } from "react";

type RevealProps = {
  children: ReactNode;
  className?: string;
  delay?: number;
};

/** Legacy section reveal — backed by shared motion tokens. */
export function Reveal({ children, className = "", delay = 0 }: RevealProps) {
  const reduceMotion = usePrefersReducedMotion();

  if (reduceMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: distances.md }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: viewport.once, margin: viewport.margin }}
      transition={{ duration: durations.slow, delay, ease: easings.out }}
    >
      {children}
    </motion.div>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  align = "left",
}: {
  eyebrow?: string;
  title: string;
  align?: "left" | "center";
}) {
  return (
    <div className={align === "center" ? "text-center" : ""}>
      {eyebrow ? (
        <SlideIn>
          <p className="mb-3 text-xs font-semibold tracking-[0.28em] text-brand-bright uppercase">
            {eyebrow}
          </p>
        </SlideIn>
      ) : null}
      <RevealText
        as="h2"
        className="font-display text-3xl font-semibold tracking-tight text-foreground sm:text-4xl md:text-5xl"
      >
        {title}
      </RevealText>
    </div>
  );
}
