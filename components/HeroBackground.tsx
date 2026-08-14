"use client";

import { withBase } from "@/lib/basePath";
import { motion, useReducedMotion } from "framer-motion";

/**
 * Layered MCP-generated hero background with Ken Burns + floating steel graphics.
 */
export function HeroBackground() {
  const reduceMotion = useReducedMotion();

  return (
    <div className="absolute inset-0 overflow-hidden" aria-hidden>
      {/* Base skyline — Ken Burns */}
      <motion.div
        className="absolute inset-[-8%]"
        initial={false}
        animate={
          reduceMotion
            ? { scale: 1.05 }
            : {
                scale: [1.08, 1.16, 1.08],
                x: ["0%", "-2%", "0%"],
                y: ["0%", "-1.5%", "0%"],
              }
        }
        transition={
          reduceMotion
            ? undefined
            : { duration: 28, repeat: Infinity, ease: "easeInOut" }
        }
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={withBase("/media/backgrounds/hero-skyline.jpg")}
          alt=""
          className="h-full w-full object-cover"
          draggable={false}
        />
      </motion.div>

      {/* Fallback video under/over blend for extra life when available */}
      <video
        className="absolute inset-0 h-full w-full object-cover opacity-35 mix-blend-lighten"
        autoPlay
        muted
        loop
        playsInline
        poster={withBase("/media/backgrounds/hero-skyline.jpg")}
      >
        <source src={withBase("/media/videos/hero-city.mp4")} type="video/mp4" />
      </video>

      {/* Floating abstract steel beams — right */}
      <motion.div
        className="absolute -right-[14%] top-[4%] h-[72%] w-[58%] opacity-45"
        animate={
          reduceMotion
            ? undefined
            : { y: [0, -22, 0], rotate: [0, 1.5, 0], opacity: [0.34, 0.52, 0.34] }
        }
        transition={{ duration: 16, repeat: Infinity, ease: "easeInOut" }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={withBase("/media/backgrounds/steel-abstract.jpg")}
          alt=""
          className="h-full w-full object-contain drop-shadow-[0_0_48px_rgba(51,153,204,0.28)]"
          draggable={false}
        />
      </motion.div>

      {/* Mirrored beam accent — left depth */}
      <motion.div
        className="absolute -left-[18%] bottom-[8%] h-[48%] w-[42%] -scale-x-100 opacity-25"
        animate={
          reduceMotion
            ? undefined
            : { y: [0, 14, 0], rotate: [0, -1, 0], opacity: [0.18, 0.3, 0.18] }
        }
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut", delay: 1.5 }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={withBase("/media/backgrounds/steel-abstract.jpg")}
          alt=""
          className="h-full w-full object-contain blur-[1px]"
          draggable={false}
        />
      </motion.div>

      {/* Brushed steel texture wash */}
      <motion.div
        className="absolute inset-0 opacity-[0.18] mix-blend-soft-light"
        animate={reduceMotion ? undefined : { opacity: [0.12, 0.22, 0.12] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={withBase("/media/backgrounds/steel-texture.jpg")}
          alt=""
          className="h-full w-full object-cover"
          draggable={false}
        />
      </motion.div>

      {/* Moving light sweep */}
      {!reduceMotion ? (
        <motion.div
          className="pointer-events-none absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-brand-bright/10 to-transparent"
          initial={{ left: "-40%" }}
          animate={{ left: ["-40%", "120%"] }}
          transition={{ duration: 9, repeat: Infinity, ease: "easeInOut", repeatDelay: 4 }}
        />
      ) : null}

      {/* Soft grid for modern tech feel */}
      <div className="absolute inset-0 steel-grid opacity-[0.12]" />

      {/* Depth gradients */}
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(11,18,24,0.62)_0%,rgba(11,18,24,0.28)_32%,rgba(11,18,24,0.42)_68%,rgba(11,18,24,0.94)_100%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_72%_38%,rgba(51,153,204,0.22),transparent_52%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_15%_80%,rgba(51,102,153,0.18),transparent_45%)]" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-56 bg-gradient-to-t from-steel-900 via-steel-900/80 to-transparent" />
    </div>
  );
}
