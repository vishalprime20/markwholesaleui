"use client";

import { easings } from "@/lib/motion/tokens";
import {
  useFinePointer,
  usePrefersReducedMotion,
} from "@/lib/motion/usePrefersReducedMotion";
import {
  motion,
  useMotionValue,
  useSpring,
  type HTMLMotionProps,
} from "framer-motion";
import {
  memo,
  useCallback,
  useRef,
  type ButtonHTMLAttributes,
  type MouseEvent,
  type ReactNode,
} from "react";

export type MagneticButtonProps = Omit<HTMLMotionProps<"button">, "children"> & {
  children: ReactNode;
  /** Max pull distance in px (desktop only) */
  strength?: number;
  className?: string;
};

function MagneticButtonBase({
  children,
  strength = 12,
  className,
  onMouseMove,
  onMouseLeave,
  type = "button",
  ...rest
}: MagneticButtonProps) {
  const reduceMotion = usePrefersReducedMotion();
  const finePointer = useFinePointer();
  const enabled = !reduceMotion && finePointer;

  const ref = useRef<HTMLButtonElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, easings.spring);
  const springY = useSpring(y, easings.spring);

  const handleMove = useCallback(
    (event: MouseEvent<HTMLButtonElement>) => {
      onMouseMove?.(event);
      if (!enabled || !ref.current) return;

      const rect = ref.current.getBoundingClientRect();
      const offsetX = event.clientX - (rect.left + rect.width / 2);
      const offsetY = event.clientY - (rect.top + rect.height / 2);
      const max = strength;

      x.set(Math.max(-max, Math.min(max, offsetX * 0.35)));
      y.set(Math.max(-max, Math.min(max, offsetY * 0.35)));
    },
    [enabled, onMouseMove, strength, x, y],
  );

  const handleLeave = useCallback(
    (event: MouseEvent<HTMLButtonElement>) => {
      onMouseLeave?.(event);
      x.set(0);
      y.set(0);
    },
    [onMouseLeave, x, y],
  );

  if (!enabled) {
    return (
      <button
        ref={ref}
        type={type}
        className={className}
        {...(rest as ButtonHTMLAttributes<HTMLButtonElement>)}
      >
        {children}
      </button>
    );
  }

  return (
    <motion.button
      ref={ref}
      type={type}
      className={className}
      style={{ x: springX, y: springY }}
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      whileTap={{ scale: 0.98 }}
      transition={easings.spring}
      {...rest}
    >
      {children}
    </motion.button>
  );
}

export const MagneticButton = memo(MagneticButtonBase);

/** Anchor variant for CTAs that navigate. */
export function MagneticLink({
  children,
  href,
  strength = 12,
  className,
  onClick,
  ...rest
}: {
  children: ReactNode;
  href: string;
  strength?: number;
  className?: string;
} & Omit<HTMLMotionProps<"a">, "href" | "children">) {
  const reduceMotion = usePrefersReducedMotion();
  const finePointer = useFinePointer();
  const enabled = !reduceMotion && finePointer;

  const ref = useRef<HTMLAnchorElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, easings.spring);
  const springY = useSpring(y, easings.spring);

  const handleMove = useCallback(
    (event: MouseEvent<HTMLAnchorElement>) => {
      if (!enabled || !ref.current) return;
      const rect = ref.current.getBoundingClientRect();
      const offsetX = event.clientX - (rect.left + rect.width / 2);
      const offsetY = event.clientY - (rect.top + rect.height / 2);
      x.set(Math.max(-strength, Math.min(strength, offsetX * 0.35)));
      y.set(Math.max(-strength, Math.min(strength, offsetY * 0.35)));
    },
    [enabled, strength, x, y],
  );

  if (!enabled) {
    return (
      <a ref={ref} href={href} className={className} onClick={onClick}>
        {children}
      </a>
    );
  }

  return (
    <motion.a
      ref={ref}
      href={href}
      className={className}
      style={{ x: springX, y: springY }}
      onMouseMove={handleMove}
      onMouseLeave={() => {
        x.set(0);
        y.set(0);
      }}
      onClick={onClick}
      whileTap={{ scale: 0.98 }}
      {...rest}
    >
      {children}
    </motion.a>
  );
}
