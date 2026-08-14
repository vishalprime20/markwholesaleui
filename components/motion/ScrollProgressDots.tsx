"use client";

import { navLinks } from "@/lib/content";
import { useActiveSection } from "@/lib/motion/useActiveSection";
import { useSmoothScrollTo } from "@/lib/motion/useSmoothScrollTo";

export function ScrollProgressDots() {
  const active = useActiveSection();
  const scrollTo = useSmoothScrollTo();

  return (
    <nav
      className="pointer-events-none fixed top-1/2 right-5 z-40 hidden -translate-y-1/2 lg:block xl:right-8"
      aria-label="Section progress"
    >
      <ul className="pointer-events-auto flex flex-col gap-3">
        {navLinks.map((link) => {
          const id = link.href.slice(1);
          const isActive = active === id;
          return (
            <li key={link.href}>
              <button
                type="button"
                aria-label={link.label}
                aria-current={isActive ? "location" : undefined}
                onClick={() => scrollTo(link.href)}
                className={`block h-2 w-2 rounded-full transition duration-300 ${
                  isActive
                    ? "scale-125 bg-brand-bright shadow-[0_0_10px_rgba(51,153,204,0.7)]"
                    : "bg-white/30 hover:bg-white/70"
                }`}
              />
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
