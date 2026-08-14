export const TOONHUB_EASE = "cubic-bezier(0.22, 1, 0.36, 1)";
export const TOONHUB_EASE_MOTION = [0.22, 1, 0.36, 1] as const;
export const TOONHUB_DURATION_MS = 900;
export const TOONHUB_DURATION_S = TOONHUB_DURATION_MS / 1000;

export const GRAIN_BG =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.08'/%3E%3C/svg%3E\")";

export const MARK_SLIDES = [
  {
    id: "home",
    ghost: "HOME",
    label: "Home",
    details:
      "Industrial wholesale supply for the concrete industry. Rebar and wire mesh supply.",
    src: "/media/products/toonhub/bars.webp",
    bg: "#081018",
    panel: "#0b1218",
  },
  {
    id: "about",
    ghost: "ABOUT",
    label: "About Us",
    details:
      "Established 2011. North East’s vertically integrated industrial metal supply-chain — warehousing, processing, and distribution for commercial concrete.",
    src: "/media/products/toonhub/wide-flange.webp",
    bg: "#0b1218",
    panel: "#121a24",
  },
  {
    id: "services",
    ghost: "SERVICES",
    label: "Services",
    details:
      "Our market trading capacity on various metals. We mark-to-market industrial metals and lumber, managing position, credit, and cash flow in real time.",
    src: "/media/products/toonhub/steel-tube.webp",
    bg: "#121a24",
    panel: "#1a2330",
  },
  {
    id: "products",
    ghost: "PRODUCTS",
    label: "Products",
    details:
      "Hot carbon and alloy steel shapes — angle, beam, channel, plate, pipe, bar, tube — plus coated, galvanized, and deep-foundation specialty products.",
    src: "/media/products/toonhub/channel.webp",
    bg: "#1a2330",
    panel: "#243041",
  },
  {
    id: "foundation",
    ghost: "FOUNDATION",
    label: "Deep Foundation",
    details:
      "Caisson pipe, H-pile beams, soldier pile, micropiles, tie-backs, support of excavation, wrakers, and threaded bar.",
    src: "/media/products/toonhub/h-pile.webp",
    bg: "#162433",
    panel: "#243041",
  },
  {
    id: "projects",
    ghost: "PROJECTS",
    label: "Projects",
    details:
      "Northeast commercial concrete and deep-foundation jobs — Brooklyn, Manhattan, Queens superstructure and supply, including 54 Noll and Tangram Plaza.",
    src: "/media/products/toonhub/pipe-pile.webp",
    bg: "#10202c",
    panel: "#336699",
  },
  {
    id: "gallery",
    ghost: "GALLERY",
    label: "Gallery",
    details:
      "Jobsite and mill photography — processed steel, foundation cages, and field deliveries across the Mark Wholesale network.",
    src: "/media/products/toonhub/wide-flange.webp",
    bg: "#0d1822",
    panel: "#3399cc",
  },
] as const;

/** @deprecated use MARK_SLIDES */
export const TOONHUB_IMAGES = MARK_SLIDES;
