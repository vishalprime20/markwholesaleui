import { ToonHubHero } from "@/components/toonhub/ToonHubHero";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Mark Wholesale | Steel Carousel",
  description:
    "Mark Wholesale Inc — industrial wholesale steel supply. About, services, products, projects, and contact.",
};

export default function ToonHubPage() {
  return (
    <main>
      <ToonHubHero />
    </main>
  );
}
