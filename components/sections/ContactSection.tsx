"use client";

import { ContactPanel } from "@/components/contact/ContactPanel";
import { ScrollReveal, SectionChapter } from "@/components/motion";
import { SectionHeading } from "@/components/Reveal";
import { contact } from "@/lib/content";

export function ContactSection() {
  return (
    <SectionChapter
      id="contact"
      index="07"
      label="Contact"
      className="border-t border-line bg-steel-800"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading eyebrow="Get in touch" title={contact.title} />
        <ScrollReveal className="mt-12">
          <ContactPanel />
        </ScrollReveal>
      </div>
    </SectionChapter>
  );
}
