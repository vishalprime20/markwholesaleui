"use client";

import { distances, durations, easings, stagger, viewport } from "@/lib/motion/tokens";
import {
  useIsMobileViewport,
  usePrefersReducedMotion,
} from "@/lib/motion/usePrefersReducedMotion";
import { motion, type Variants } from "framer-motion";
import { Children, isValidElement, memo, type ReactNode } from "react";

export type StaggerChildrenProps = {
  children: ReactNode;
  className?: string;
  itemClassName?: string;
  delay?: number;
  staggerDelay?: number;
  /** Distance each child travels on enter */
  distance?: number;
};

function StaggerChildrenBase({
  children,
  className,
  itemClassName,
  delay = 0,
  staggerDelay,
  distance,
}: StaggerChildrenProps) {
  const reduceMotion = usePrefersReducedMotion();
  const isMobile = useIsMobileViewport();

  if (reduceMotion) {
    return <div className={className}>{children}</div>;
  }

  const y = distance ?? (isMobile ? distances.xs : distances.sm);
  const childStagger = staggerDelay ?? stagger.base;

  const container: Variants = {
    hidden: {},
    visible: {
      transition: {
        delayChildren: delay,
        staggerChildren: childStagger,
      },
    },
  };

  const item: Variants = {
    hidden: { opacity: 0, y },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: durations.base, ease: easings.out },
    },
  };

  return (
    <motion.div
      className={className}
      initial="hidden"
      whileInView="visible"
      viewport={{
        once: viewport.once,
        amount: 0.15,
        margin: viewport.margin,
      }}
      variants={container}
    >
      {Children.map(children, (child, index) => {
        if (!isValidElement(child)) {
          return (
            <motion.div key={`stagger-${index}`} className={itemClassName} variants={item}>
              {child}
            </motion.div>
          );
        }

        return (
          <motion.div key={child.key ?? `stagger-${index}`} className={itemClassName} variants={item}>
            {child}
          </motion.div>
        );
      })}
    </motion.div>
  );
}

/**
 * Use inside a custom parent that already provides stagger variants.
 */
export const StaggerItem = memo(function StaggerItem({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      className={className}
      variants={{
        hidden: { opacity: 0, y: distances.sm },
        visible: {
          opacity: 1,
          y: 0,
          transition: { duration: durations.base, ease: easings.out },
        },
      }}
    >
      {children}
    </motion.div>
  );
});

export const StaggerChildren = memo(StaggerChildrenBase);
