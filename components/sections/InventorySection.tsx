"use client";

import { SectionChapter, StaggerChildren } from "@/components/motion";
import { SectionHeading } from "@/components/Reveal";
import { inventoryProducts } from "@/lib/content";
import { motion } from "framer-motion";
import Image from "next/image";

export function InventorySection() {
  return (
    <SectionChapter
      id="inventory"
      index="01"
      label="Inventory"
      className="border-t border-line bg-steel-800"
    >
      <div className="absolute inset-0 steel-grid opacity-30" />
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading eyebrow="Inventory" title="Products & Inventory" />
        <StaggerChildren className="mt-12 grid grid-cols-2 gap-3 sm:grid-cols-3 md:gap-4 lg:grid-cols-4">
          {inventoryProducts.map((product) => (
            <motion.article
              key={product.name}
              whileHover={{ y: -6, rotateX: 2, rotateY: -2 }}
              transition={{ type: "spring", stiffness: 260, damping: 20 }}
              className="group relative overflow-hidden border border-line bg-steel-700/60"
              style={{ transformStyle: "preserve-3d" }}
            >
              <div className="relative aspect-[4/3] bg-gradient-to-b from-steel-600/40 to-steel-900/80 p-4">
                <Image
                  src={product.image}
                  alt={product.name}
                  fill
                  className="object-contain p-3 transition duration-500 group-hover:scale-105"
                  sizes="(max-width:768px) 50vw, 25vw"
                />
              </div>
              <div className="border-t border-line px-3 py-3">
                <h3 className="font-display text-sm font-semibold tracking-wide text-foreground sm:text-base">
                  {product.name}
                </h3>
              </div>
            </motion.article>
          ))}
        </StaggerChildren>
      </div>
    </SectionChapter>
  );
}
