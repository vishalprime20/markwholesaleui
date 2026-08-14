"use client";

import { MagneticLink } from "@/components/motion";
import { BrandMark } from "@/components/LogoIntro";
import { navLinks } from "@/lib/content";
import { useActiveSection } from "@/lib/motion/useActiveSection";
import { useScrollProgress } from "@/lib/motion/useScrollProgress";
import { useAnchorClick } from "@/lib/motion/useSmoothScrollTo";
import { AnimatePresence, motion, useTransform } from "framer-motion";
import Link from "next/link";
import { useEffect, useState } from "react";

export function StickyNav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const active = useActiveSection();
  const progress = useScrollProgress();
  const scaleX = useTransform(progress, [0, 1], [0, 1]);
  const onAnchor = useAnchorClick(() => setOpen(false));

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-500 ${
        scrolled
          ? "border-b border-white/10 bg-steel-900/80 backdrop-blur-2xl"
          : "bg-gradient-to-b from-steel-900/70 to-transparent"
      }`}
    >
      <motion.div
        className="absolute inset-x-0 bottom-0 h-[2px] origin-left bg-brand-bright"
        style={{ scaleX }}
        aria-hidden
      />

      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:h-[4.5rem] sm:px-6 lg:px-8">
        <a
          href="#home"
          className="relative z-10 flex items-center"
          aria-label="Mark Wholesale home"
          onClick={onAnchor}
        >
          <BrandMark className="h-8 sm:h-9" variant="white" />
        </a>

        <nav className="hidden items-center gap-0.5 lg:flex" aria-label="Primary">
          {navLinks
            .filter((link) => link.href !== "#contact")
            .map((link) => {
              const isActive = active === link.href.slice(1);
              return (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={onAnchor}
                  aria-current={isActive ? "location" : undefined}
                  className={`relative px-3.5 py-2 text-[13px] font-medium tracking-wide transition ${
                    isActive ? "text-white" : "text-white/70 hover:text-white"
                  }`}
                >
                  {link.label}
                  {isActive ? (
                    <span className="absolute inset-x-3.5 -bottom-0.5 h-px bg-brand-bright" />
                  ) : null}
                </a>
              );
            })}
          <MagneticLink
            href="#contact"
            onClick={onAnchor}
            className="ml-3 inline-flex bg-brand-bright px-4 py-2 text-[13px] font-semibold tracking-wide text-steel-900 transition hover:bg-[#4db0df]"
          >
            Contact
          </MagneticLink>
          <Link
            href="/toonhub"
            className="ml-2 px-3.5 py-2 text-[13px] font-medium tracking-wide text-white/70 transition hover:text-white"
          >
            Demo v2
          </Link>
        </nav>

        <button
          type="button"
          className="relative z-10 inline-flex h-10 w-10 items-center justify-center border border-white/20 text-white lg:hidden"
          aria-expanded={open}
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen((v) => !v)}
        >
          <span className="sr-only">Menu</span>
          <div className="flex w-5 flex-col gap-1.5">
            <span className={`h-0.5 bg-current transition ${open ? "translate-y-2 rotate-45" : ""}`} />
            <span className={`h-0.5 bg-current transition ${open ? "opacity-0" : ""}`} />
            <span className={`h-0.5 bg-current transition ${open ? "-translate-y-2 -rotate-45" : ""}`} />
          </div>
        </button>
      </div>

      <AnimatePresence>
        {open && (
          <motion.nav
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="border-b border-white/10 bg-steel-900/95 px-4 py-6 backdrop-blur-2xl lg:hidden"
            aria-label="Mobile"
          >
            <ul className="flex flex-col gap-1">
              {navLinks.map((link) => {
                const isActive = active === link.href.slice(1);
                return (
                  <li key={link.href}>
                    <a
                      href={link.href}
                      className={`block px-3 py-3 text-base font-medium ${
                        isActive ? "text-brand-bright" : "text-white/85 hover:text-brand-bright"
                      }`}
                      aria-current={isActive ? "location" : undefined}
                      onClick={onAnchor}
                    >
                      {link.label}
                    </a>
                  </li>
                );
              })}
              <li>
                <Link
                  href="/toonhub"
                  className="block px-3 py-3 text-base font-medium text-white/85 hover:text-brand-bright"
                  onClick={() => setOpen(false)}
                >
                  Demo v2
                </Link>
              </li>
            </ul>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  );
}
