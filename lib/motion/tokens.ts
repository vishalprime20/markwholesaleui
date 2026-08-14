/**
 * Shared motion design tokens — premium, subtle, consistent.
 */

export const easings = {
  /** Primary UI ease (smooth deceleration) */
  out: [0.22, 1, 0.36, 1] as const,
  /** Soft entrance */
  soft: [0.16, 1, 0.3, 1] as const,
  /** Magnetic / pointer follow */
  spring: { type: "spring" as const, stiffness: 280, damping: 22, mass: 0.6 },
  /** CSS cubic-bezier string for GSAP */
  outCss: "cubic-bezier(0.22, 1, 0.36, 1)",
} as const;

export const durations = {
  instant: 0.01,
  fast: 0.35,
  base: 0.55,
  slow: 0.75,
  slower: 0.95,
  /** GSAP scroll reveals */
  scroll: 0.9,
} as const;

export const distances = {
  xs: 8,
  sm: 16,
  md: 24,
  lg: 36,
  /** Mobile-capped parallax (px) */
  parallaxMobile: 24,
  parallaxDesktop: 64,
} as const;

export const stagger = {
  tight: 0.04,
  base: 0.07,
  loose: 0.11,
} as const;

export const viewport = {
  once: true,
  amount: 0.25,
  margin: "-8% 0px",
} as const;

export const scrollTriggerDefaults = {
  start: "top 85%",
  end: "bottom 15%",
  once: true,
  toggleActions: "play none none none",
} as const;
