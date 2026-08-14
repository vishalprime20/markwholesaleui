import type { Metadata } from "next";
import { Outfit, Syne } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  display: "swap",
});

const syne = Syne({
  variable: "--font-syne",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Industrial Wholesale Supply | Mark Wholesale Inc | New York",
  description:
    "Mark Wholesale Inc — industrial wholesale supply for the concrete industry. Rebar, wire mesh, structural steel, deep foundation products across the Northeast.",
  openGraph: {
    title: "Mark Wholesale Inc | Industrial Wholesale Supply",
    description:
      "Vertically integrated industrial metal supply-chain, warehousing, processing & distribution for commercial concrete projects.",
    type: "website",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${outfit.variable} ${syne.variable} h-full antialiased`}>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full font-sans text-foreground antialiased">{children}</body>
    </html>
  );
}
