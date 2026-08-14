"use client";

import { ParallaxElement, ScrollReveal, SectionChapter, StaggerChildren } from "@/components/motion";
import { SectionHeading } from "@/components/Reveal";
import { completedProjects, featuredProjects } from "@/lib/content";
import Image from "next/image";

export function ProjectsSection() {
  return (
    <SectionChapter
      id="projects"
      index="05"
      label="Projects"
      className="border-y border-line bg-steel-800"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading eyebrow="Portfolio" title="Projects" />

        <StaggerChildren className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {featuredProjects.map((project) => (
            <article
              key={project.title}
              className="group overflow-hidden border border-line bg-steel-900/40"
            >
              <div className="relative aspect-[16/10] overflow-hidden">
                <ParallaxElement
                  speed={24}
                  className="absolute inset-x-0 -top-[12%] h-[124%] w-full will-change-transform"
                >
                  <div className="relative h-full w-full">
                    <Image
                      src={project.image}
                      alt={project.title}
                      fill
                      className="object-cover transition duration-700 group-hover:scale-105"
                      sizes="(max-width:1024px) 50vw, 33vw"
                    />
                  </div>
                </ParallaxElement>
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-steel-900 via-steel-900/20 to-transparent" />
              </div>
              <div className="px-4 py-4">
                <h3 className="font-display text-base font-semibold text-foreground sm:text-lg">
                  {project.title}
                </h3>
              </div>
            </article>
          ))}
        </StaggerChildren>

        <ScrollReveal delay={0.1} className="mt-16">
          <h3 className="font-display text-xl font-semibold text-foreground sm:text-2xl">
            Project’s Completed
          </h3>
          <ul className="mt-6 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {completedProjects.map((item) => (
              <li
                key={item}
                className="border-l-2 border-brand-bright/60 bg-steel-900/30 px-4 py-3 text-sm text-muted"
              >
                {item}
              </li>
            ))}
          </ul>
        </ScrollReveal>
      </div>
    </SectionChapter>
  );
}
