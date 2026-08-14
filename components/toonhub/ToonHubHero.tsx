"use client";

import { HeroBackground } from "@/components/HeroBackground";
import { ToonHubContactOverlay } from "@/components/toonhub/ToonHubContactOverlay";
import { ToonHubMenu } from "@/components/toonhub/ToonHubMenu";
import { ToonHubSlideCopy } from "@/components/toonhub/ToonHubSlideCopy";
import { withBase } from "@/lib/basePath";
import {
  GRAIN_BG,
  MARK_SLIDES,
  TOONHUB_DURATION_MS,
  TOONHUB_DURATION_S,
  TOONHUB_EASE,
  TOONHUB_EASE_MOTION,
} from "@/lib/toonhub";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

const SLIDES = MARK_SLIDES;
const N = SLIDES.length;

type Role = "center" | "left" | "right" | "back" | "hidden";

function roleFor(index: number, activeIndex: number): Role {
  if (index === activeIndex) return "center";
  if (index === (activeIndex + N - 1) % N) return "left";
  if (index === (activeIndex + 1) % N) return "right";
  if (index === (activeIndex + 2) % N) return "back";
  return "hidden";
}

function roleAnimate(role: Role, isMobile: boolean) {
  const shift = isMobile ? 18 : 26;

  if (role === "center") {
    return {
      left: `${50 + shift}%`,
      top: "48%",
      x: "-50%",
      y: "-50%",
      scale: isMobile ? 1 : 1.12,
      rotateY: 0,
      height: isMobile ? "52%" : "68%",
      opacity: 1,
      filter: "blur(0px)",
      zIndex: 20,
    };
  }

  if (role === "left") {
    return {
      left: isMobile ? `${20 + shift}%` : `${30 + shift}%`,
      top: isMobile ? "42%" : "52%",
      x: "-50%",
      y: "-50%",
      scale: 0.92,
      rotateY: 18,
      height: isMobile ? "18%" : "28%",
      opacity: 0.82,
      filter: "blur(2px)",
      zIndex: 10,
    };
  }

  if (role === "right") {
    return {
      left: isMobile ? `${80 + shift}%` : `${70 + shift}%`,
      top: isMobile ? "42%" : "52%",
      x: "-50%",
      y: "-50%",
      scale: 0.92,
      rotateY: -18,
      height: isMobile ? "18%" : "28%",
      opacity: 0.82,
      filter: "blur(2px)",
      zIndex: 10,
    };
  }

  if (role === "back") {
    return {
      left: `${50 + shift}%`,
      top: isMobile ? "38%" : "48%",
      x: "-50%",
      y: "-50%",
      scale: 0.78,
      rotateY: 0,
      height: isMobile ? "14%" : "22%",
      opacity: 0.7,
      filter: "blur(4px)",
      zIndex: 5,
    };
  }

  return {
    left: `${50 + shift}%`,
    top: "50%",
    x: "-50%",
    y: "-50%",
    scale: 0.62,
    rotateY: 0,
    height: isMobile ? "10%" : "16%",
    opacity: 0,
    filter: "blur(8px)",
    zIndex: 1,
  };
}

export function ToonHubHero() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isMobile, setIsMobile] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [contactOpen, setContactOpen] = useState(false);
  const animatingRef = useRef(false);
  const blockedRef = useRef(false);
  const touchStartY = useRef(0);
  const touchOnGallery = useRef(false);
  const copyScrollRef = useRef<HTMLDivElement>(null);

  const lockUntilDone = useCallback(() => {
    animatingRef.current = true;
    window.setTimeout(() => {
      animatingRef.current = false;
    }, TOONHUB_DURATION_MS);
  }, []);

  useEffect(() => {
    SLIDES.forEach((item) => {
      const img = new Image();
      img.src = withBase(item.src);
    });
  }, []);

  useEffect(() => {
    const update = () => setIsMobile(window.innerWidth < 640);
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  useEffect(() => {
    blockedRef.current = menuOpen || contactOpen;
  }, [contactOpen, menuOpen]);

  const navigate = useCallback(
    (dir: "next" | "prev") => {
      if (animatingRef.current || blockedRef.current) return;
      lockUntilDone();
      setActiveIndex((prev) => (dir === "next" ? (prev + 1) % N : (prev + N - 1) % N));
    },
    [lockUntilDone],
  );

  const goToIndex = useCallback(
    (index: number) => {
      if (!Number.isInteger(index) || index < 0 || index >= N) return;
      if (index === activeIndex || animatingRef.current || blockedRef.current) return;
      lockUntilDone();
      setActiveIndex(index);
    },
    [activeIndex, lockUntilDone],
  );

  const goToSection = useCallback(
    (sectionId: string) => {
      goToIndex(SLIDES.findIndex((slide) => slide.id === sectionId));
    },
    [goToIndex],
  );

  useEffect(() => {
    if (typeof activeIndex !== "number" || activeIndex < 0 || activeIndex >= N) {
      setActiveIndex(0);
    }
  }, [activeIndex]);

  useEffect(() => {
    copyScrollRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }, [activeIndex]);

  useEffect(() => {
    const onWheel = (event: WheelEvent) => {
      if (blockedRef.current) return;
      const gallery = (event.target as HTMLElement | null)?.closest?.("[data-gallery-slider]");
      if (gallery) return;
      const copy = (event.target as HTMLElement | null)?.closest?.("[data-copy-scroll]");
      if (copy) {
        const el = copy as HTMLElement;
        const atTop = el.scrollTop <= 0 && event.deltaY < 0;
        const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 1 && event.deltaY > 0;
        const canScroll = el.scrollHeight > el.clientHeight && !atTop && !atBottom;
        if (canScroll || (!atTop && !atBottom)) return;
      }
      event.preventDefault();
      if (Math.abs(event.deltaY) < 10) return;
      navigate(event.deltaY > 0 ? "next" : "prev");
    };

    const onTouchStart = (event: TouchEvent) => {
      touchStartY.current = event.touches[0]?.clientY ?? 0;
      touchOnGallery.current = Boolean(
        (event.target as HTMLElement | null)?.closest?.("[data-gallery-slider]"),
      );
    };

    const onTouchEnd = (event: TouchEvent) => {
      if (blockedRef.current || touchOnGallery.current) return;
      const endY = event.changedTouches[0]?.clientY ?? touchStartY.current;
      const dy = touchStartY.current - endY;
      if (Math.abs(dy) < 40) return;
      navigate(dy > 0 ? "next" : "prev");
    };

    window.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchend", onTouchEnd, { passive: true });
    return () => {
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("touchstart", onTouchStart);
      window.removeEventListener("touchend", onTouchEnd);
    };
  }, [navigate]);

  const active = SLIDES[typeof activeIndex === "number" && activeIndex >= 0 && activeIndex < N ? activeIndex : 0];

  return (
    <div
      className="relative w-full overflow-hidden"
      id="discover"
      style={{
        fontFamily: "'Inter', sans-serif",
      }}
    >
      <div className="relative w-full" style={{ height: "100vh", overflow: "hidden" }}>
        <HeroBackground />
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            zIndex: 1,
            backgroundColor: active.bg,
            opacity: active.id === "home" ? 0.28 : 0.62,
            transition: `background-color ${TOONHUB_DURATION_MS}ms ${TOONHUB_EASE}, opacity ${TOONHUB_DURATION_MS}ms ${TOONHUB_EASE}`,
          }}
          aria-hidden
        />
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            zIndex: 50,
            opacity: 0.4,
            backgroundImage: GRAIN_BG,
            backgroundSize: "200px 200px",
            backgroundRepeat: "repeat",
          }}
          aria-hidden
        />

        <div
          className="pointer-events-none absolute inset-x-0 flex select-none items-center justify-center"
          style={{ zIndex: 2, top: "18%" }}
          aria-hidden
        >
          <p
            key={active.ghost}
            className="uppercase"
            style={{
              fontFamily: "'Anton', sans-serif",
              fontSize: "clamp(42px, 10vw, 120px)",
              fontWeight: 900,
              color: "white",
              opacity: 0,
              lineHeight: 1,
              letterSpacing: "-0.02em",
              whiteSpace: "nowrap",
              transition: `opacity ${TOONHUB_DURATION_MS}ms ${TOONHUB_EASE}`,
            }}
          >
            {active.ghost}
          </p>
        </div>

        <ToonHubMenu
          activeId={active.id}
          open={menuOpen}
          onOpenChange={setMenuOpen}
          onGoTo={goToSection}
          onContact={() => setContactOpen(true)}
        />

        <div className="absolute inset-0" style={{ zIndex: 3, perspective: 1400 }}>
          {SLIDES.map((item, index) => {
            const role = roleFor(index, activeIndex);
            return (
              <motion.div
                key={item.id}
                initial={false}
                animate={roleAnimate(role, isMobile)}
                transition={{
                  duration: TOONHUB_DURATION_S,
                  ease: TOONHUB_EASE_MOTION,
                  zIndex: { duration: 0, delay: role === "center" ? 0 : TOONHUB_DURATION_S * 0.35 },
                }}
                style={{
                  position: "absolute",
                  aspectRatio: "0.6 / 1",
                  pointerEvents: "none",
                  transformStyle: "preserve-3d",
                  willChange: "transform, filter, opacity, height, left, top",
                }}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={withBase(item.src)}
                  alt={item.label}
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "contain",
                    objectPosition: "center",
                  }}
                  draggable={false}
                />
              </motion.div>
            );
          })}
        </div>

        <div
          ref={copyScrollRef}
          className="absolute bottom-24 left-4 z-[60] flex max-h-[calc(100svh-8.5rem)] w-[min(92vw,620px)] flex-col justify-end overflow-hidden overflow-x-hidden pr-2 sm:left-8 sm:bottom-28 lg:left-12 lg:w-[min(50vw,680px)]"
        >
          <AnimatePresence initial={false}>
            <motion.div
              key={active.id}
              initial={{ opacity: 0, y: 40, filter: "blur(10px)" }}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              exit={{
                opacity: 0,
                y: -32,
                filter: "blur(10px)",
                position: "absolute",
                width: "100%",
                left: 0,
                top: 0,
              }}
              transition={{ duration: TOONHUB_DURATION_S, ease: TOONHUB_EASE_MOTION }}
            >
              <ToonHubSlideCopy
                sectionId={active.id}
                onContact={() => setContactOpen(true)}
                onViewProducts={() => goToSection("products")}
              />
            </motion.div>
          </AnimatePresence>
        </div>

        <button
          type="button"
          className="font-display absolute right-4 bottom-6 z-[60] flex items-center gap-2 text-[clamp(1.65rem,3.8vh,2.5rem)] font-semibold tracking-tight text-white uppercase no-underline opacity-95 transition hover:opacity-100 sm:right-10 sm:bottom-20"
          onClick={() => setContactOpen(true)}
        >
          CONTACT US
          <ArrowRight className="h-5 w-5 sm:h-6 sm:w-6" strokeWidth={2.25} />
        </button>
      </div>

      <ToonHubContactOverlay
        open={contactOpen}
        onClose={() => setContactOpen(false)}
        onHome={() => {
          setContactOpen(false);
          blockedRef.current = false;
          goToSection("home");
        }}
      />
    </div>
  );
}
