import { Anton, Inter } from "next/font/google";
import type { ReactNode } from "react";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-toonhub-inter",
  display: "swap",
});

const anton = Anton({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-toonhub-anton",
  display: "swap",
});

export default function ToonHubLayout({ children }: { children: ReactNode }) {
  return (
    <div className={`${inter.className} ${inter.variable} ${anton.variable} min-h-svh bg-black`}>
      {children}
    </div>
  );
}
