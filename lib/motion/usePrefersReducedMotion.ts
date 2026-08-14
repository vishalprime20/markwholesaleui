"use client";

import { useReducedMotion } from "framer-motion";
import { useEffect, useState, useSyncExternalStore } from "react";

const QUERY = "(prefers-reduced-motion: reduce)";
const FINE_POINTER = "(pointer: fine)";
const MOBILE_MAX = "(max-width: 767px)";

function subscribeMedia(query: string, onChange: () => void) {
  const mql = window.matchMedia(query);
  mql.addEventListener("change", onChange);
  return () => mql.removeEventListener("change", onChange);
}

function getMediaSnapshot(query: string) {
  return window.matchMedia(query).matches;
}

/**
 * Stable reduced-motion flag (Framer Motion + SSR-safe fallback).
 */
export function usePrefersReducedMotion(): boolean {
  const framer = useReducedMotion();
  const fallback = useSyncExternalStore(
    (cb) => (typeof window === "undefined" ? () => {} : subscribeMedia(QUERY, cb)),
    () => getMediaSnapshot(QUERY),
    () => false,
  );
  return framer ?? fallback;
}

export function useFinePointer(): boolean {
  return useSyncExternalStore(
    (cb) => (typeof window === "undefined" ? () => {} : subscribeMedia(FINE_POINTER, cb)),
    () => getMediaSnapshot(FINE_POINTER),
    () => false,
  );
}

export function useIsMobileViewport(): boolean {
  return useSyncExternalStore(
    (cb) => (typeof window === "undefined" ? () => {} : subscribeMedia(MOBILE_MAX, cb)),
    () => getMediaSnapshot(MOBILE_MAX),
    () => true,
  );
}

/** Mount gate — avoids hydration mismatch on client-only animation mounts. */
export function useHasMounted(): boolean {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  return mounted;
}
