"use client";

import { Hero } from "@/components/Hero";
import { LogoIntro } from "@/components/LogoIntro";
import { SiteFooter } from "@/components/SiteFooter";
import { SmoothScroll } from "@/components/SmoothScroll";
import { StickyNav } from "@/components/StickyNav";
import { ScrollProgressDots } from "@/components/motion";
import { AboutSection } from "@/components/sections/AboutSection";
import { ContactSection } from "@/components/sections/ContactSection";
import { GallerySection } from "@/components/sections/GallerySection";
import { InventorySection } from "@/components/sections/InventorySection";
import { ProductsSection } from "@/components/sections/ProductsSection";
import { ProjectsSection } from "@/components/sections/ProjectsSection";
import { ServicesSection } from "@/components/sections/ServicesSection";
import { useCallback, useState, useSyncExternalStore } from "react";

function subscribeNoop() {
  return () => {};
}

function getMounted() {
  return true;
}

function getNotMounted() {
  return false;
}

function getPrefersReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function HomePage() {
  const mounted = useSyncExternalStore(subscribeNoop, getMounted, getNotMounted);
  const reduceMotion = useSyncExternalStore(
    subscribeNoop,
    () => (mounted ? getPrefersReducedMotion() : true),
    () => true,
  );
  const [finished, setFinished] = useState(false);
  const showIntro = mounted && !reduceMotion && !finished;
  const introComplete = !mounted || reduceMotion || finished;

  const onIntroComplete = useCallback(() => {
    setFinished(true);
  }, []);

  return (
    <SmoothScroll>
      {showIntro ? <LogoIntro onComplete={onIntroComplete} /> : null}
      <StickyNav />
      <ScrollProgressDots />
      <main>
        <Hero introComplete={introComplete} />
        <InventorySection />
        <AboutSection />
        <ServicesSection />
        <ProductsSection />
        <ProjectsSection />
        <GallerySection />
        <ContactSection />
      </main>
      <SiteFooter />
    </SmoothScroll>
  );
}
