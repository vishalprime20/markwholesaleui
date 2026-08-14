"use client";

import { BrandMark } from "@/components/LogoIntro";
import { MagneticLink } from "@/components/motion";
import { navLinks } from "@/lib/content";
import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { useEffect } from "react";

const DESKTOP_LINKS = navLinks.filter((link) => link.href !== "#contact");

function sectionIdFromHref(href: string) {
  return href.slice(1);
}

export function ToonHubMenu({
  activeId,
  open,
  onOpenChange,
  onGoTo,
  onContact,
}: {
  activeId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGoTo: (sectionId: string) => void;
  onContact: () => void;
}) {
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  const go = (sectionId: string) => {
    onGoTo(sectionId);
    onOpenChange(false);
  };

  const isActive = (href: string) => {
    const id = sectionIdFromHref(href);
    if (id === "products") return activeId === "products" || activeId === "foundation";
    return activeId === id;
  };

  return (
    <header className="absolute inset-x-0 top-0 z-[70] bg-gradient-to-b from-steel-900/70 to-transparent">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:h-[4.5rem] sm:px-6 lg:px-8">
        <button
          type="button"
          className="relative z-10 flex items-center"
          aria-label="Mark Wholesale home"
          onClick={() => go("home")}
        >
          <BrandMark className="h-8 sm:h-9" variant="white" />
        </button>

        <nav className="hidden items-center gap-0.5 lg:flex" aria-label="Primary">
          {DESKTOP_LINKS.map((link) => {
            const active = isActive(link.href);
            return (
              <button
                key={link.href}
                type="button"
                onClick={() => go(sectionIdFromHref(link.href))}
                aria-current={active ? "location" : undefined}
                className={`relative px-3.5 py-2 text-[13px] font-medium tracking-wide transition ${
                  active ? "text-white" : "text-white/70 hover:text-white"
                }`}
              >
                {link.label}
                {active ? (
                  <span className="absolute inset-x-3.5 -bottom-0.5 h-px bg-brand-bright" />
                ) : null}
              </button>
            );
          })}
          <MagneticLink
            href="#contact"
            onClick={(event) => {
              event.preventDefault();
              onOpenChange(false);
              onContact();
            }}
            className="ml-3 inline-flex bg-brand-bright px-4 py-2 text-[13px] font-semibold tracking-wide text-steel-900 transition hover:bg-[#4db0df]"
          >
            Contact
          </MagneticLink>
          <Link
            href="/"
            className="ml-2 px-3.5 py-2 text-[13px] font-medium tracking-wide text-white/70 transition hover:text-white"
          >
            Main Site
          </Link>
          <Link
            href="/toonhub"
            onClick={(event) => {
              event.preventDefault();
              go("home");
            }}
            className="px-3.5 py-2 text-[13px] font-medium tracking-wide text-white transition hover:text-white"
            aria-current="page"
          >
            Demo v2
          </Link>
        </nav>

        <button
          type="button"
          className="relative z-10 inline-flex h-10 w-10 items-center justify-center border border-white/20 text-white lg:hidden"
          aria-expanded={open}
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => onOpenChange(!open)}
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
                const id = sectionIdFromHref(link.href);
                const active = isActive(link.href);
                return (
                  <li key={link.href}>
                    <button
                      type="button"
                      className={`block w-full px-3 py-3 text-left text-base font-medium ${
                        active ? "text-brand-bright" : "text-white/85 hover:text-brand-bright"
                      }`}
                      aria-current={active ? "location" : undefined}
                      onClick={() => {
                        if (id === "contact") {
                          onOpenChange(false);
                          onContact();
                          return;
                        }
                        go(id);
                      }}
                    >
                      {link.label}
                    </button>
                  </li>
                );
              })}
              <li>
                <Link
                  href="/"
                  className="block px-3 py-3 text-base font-medium text-white/85 hover:text-brand-bright"
                  onClick={() => onOpenChange(false)}
                >
                  Main Site
                </Link>
              </li>
              <li>
                <Link
                  href="/toonhub"
                  className="block px-3 py-3 text-base font-medium text-brand-bright"
                  aria-current="page"
                  onClick={(event) => {
                    event.preventDefault();
                    go("home");
                  }}
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
