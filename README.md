# Mark Wholesale UI

Modern 2026 rebuild of [markwholesale.com](https://www.markwholesale.com/) — single-page industrial marketing site with motion, 3D hero accents, and the original site content.

## Stack

- Next.js (App Router) + TypeScript
- Tailwind CSS
- Framer Motion
- React Three Fiber / Drei
- Lenis smooth scroll

## Develop

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Build

```bash
npm run build
npm start
```

## Assets

Original media lives in `MW_Site_Files/`. Curated copies used by the site are in `public/media/`.

## Notes

- Contact form is UI-only (shows success state; no backend).
- Logo intro plays the transparent PNG frame sequence (`_afr_*.png`, inverted for the dark UI) on every refresh; respects `prefers-reduced-motion`.
- Nav/footer use `MarkWholesale_logo_transparent_white.png`.
- Source assets: `MW_Site_Files/Logos and Animations/` → `public/media/logos/`.
- Hero 3D steel shapes load on desktop only; mobile uses a lightweight CSS fallback.
