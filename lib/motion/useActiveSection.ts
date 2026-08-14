"use client";

import { SPY_SECTION_IDS } from "@/lib/motion/useSmoothScrollTo";
import { useLenis } from "lenis/react";
import { useCallback, useEffect, useState } from "react";

function readActive(ids: readonly string[]) {
  const line = window.innerHeight * 0.28;
  let current = ids[0] ?? "";
  for (const id of ids) {
    const el = document.getElementById(id);
    if (!el) continue;
    if (el.getBoundingClientRect().top <= line) current = id;
  }
  return current;
}

export function useActiveSection(ids: readonly string[] = SPY_SECTION_IDS) {
  const [active, setActive] = useState(ids[0] ?? "home");

  const update = useCallback(() => {
    setActive((prev) => {
      const next = readActive(ids);
      return next === prev ? prev : next;
    });
  }, [ids]);

  useLenis(update);

  useEffect(() => {
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [update]);

  return active;
}
