"use client";

import { durations, easings, stagger, viewport } from "@/lib/motion/tokens";
import { usePrefersReducedMotion } from "@/lib/motion/usePrefersReducedMotion";
import { motion, type Variants } from "framer-motion";
import { memo, useMemo, type ReactNode } from "react";

export type RevealTextProps = {
  children: string;
  className?: string;
  delay?: number;
  /** Split by word (default) or character */
  by?: "word" | "char";
  as?: "p" | "h1" | "h2" | "h3" | "h4" | "span" | "div";
};

const containerVariants = (delay: number, childStagger: number): Variants => ({
  hidden: {},
  visible: {
    transition: {
      delayChildren: delay,
      staggerChildren: childStagger,
    },
  },
});

const itemVariants: Variants = {
  hidden: { opacity: 0, y: "0.45em" },
  visible: {
    opacity: 1,
    y: "0em",
    transition: {
      duration: durations.base,
      ease: easings.out,
    },
  },
};

function RevealTextBase({
  children,
  className,
  delay = 0,
  by = "word",
  as = "p",
}: RevealTextProps) {
  const reduceMotion = usePrefersReducedMotion();
  const MotionTag = motion[as];

  const parts = useMemo(() => {
    if (by === "char") return Array.from(children);
    return children.split(/(\s+)/);
  }, [by, children]);

  if (reduceMotion) {
    const Tag = as;
    return <Tag className={className}>{children}</Tag>;
  }

  return (
    <MotionTag
      className={className}
      initial="hidden"
      whileInView="visible"
      viewport={{
        once: viewport.once,
        amount: viewport.amount,
        margin: viewport.margin,
      }}
      variants={containerVariants(delay, by === "char" ? stagger.tight : stagger.base)}
      aria-label={children}
    >
      {parts.map((part, i) => {
        if (by === "word" && /^\s+$/.test(part)) {
          return <span key={`s-${i}`}>{part}</span>;
        }

        return (
          <span key={`${part}-${i}`} className="inline-block overflow-hidden align-bottom">
            <motion.span className="inline-block" variants={itemVariants}>
              {part === " " ? "\u00A0" : part}
            </motion.span>
          </span>
        );
      })}
    </MotionTag>
  );
}

export const RevealText = memo(RevealTextBase);

/** Optional wrapper when you need non-string children with the same entrance. */
export function RevealTextBlock({
  children,
  className,
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  const reduceMotion = usePrefersReducedMotion();
  if (reduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{
        once: viewport.once,
        amount: viewport.amount,
        margin: viewport.margin,
      }}
      transition={{ duration: durations.slow, delay, ease: easings.out }}
    >
      {children}
    </motion.div>
  );
}
