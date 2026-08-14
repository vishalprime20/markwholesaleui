"use client";

import { FadeIn, MagneticButton } from "@/components/motion";
import { contact } from "@/lib/content";
import { MediaImage as Image } from "@/components/MediaImage";
import { FormEvent, useState } from "react";

export function ContactPanel({ idPrefix = "", compact = false }: { idPrefix?: string; compact?: boolean }) {
  const [submitted, setSubmitted] = useState(false);

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitted(true);
  }

  const nameId = `${idPrefix}name`;
  const emailId = `${idPrefix}email`;
  const messageId = `${idPrefix}message`;

  return (
    <div className={`grid lg:grid-cols-2 ${compact ? "h-full gap-6" : "gap-12"}`}>
      {submitted ? (
        <FadeIn immediate>
          <div
            className={`flex items-center justify-center border border-brand-bright/40 bg-steel-900/50 px-6 text-center ${
              compact ? "min-h-[200px] py-10" : "min-h-[280px] py-16"
            }`}
          >
            <p className="font-display text-2xl font-semibold text-brand-bright">{contact.success}</p>
          </div>
        </FadeIn>
      ) : (
        <form
          onSubmit={onSubmit}
          className={`border border-line bg-steel-900/40 ${compact ? "space-y-2.5 p-4" : "space-y-4 p-6 sm:p-8"}`}
        >
          <div>
            <label htmlFor={nameId} className="mb-1.5 block text-xs tracking-wide text-muted uppercase">
              Name
            </label>
            <input
              id={nameId}
              name="name"
              required
              className={`w-full border border-line bg-steel-800 px-3 text-sm text-foreground outline-none transition focus:border-brand-bright ${
                compact ? "py-2" : "py-3"
              }`}
            />
          </div>
          <div>
            <label htmlFor={emailId} className="mb-1.5 block text-xs tracking-wide text-muted uppercase">
              Email
            </label>
            <input
              id={emailId}
              name="email"
              type="email"
              required
              className={`w-full border border-line bg-steel-800 px-3 text-sm text-foreground outline-none transition focus:border-brand-bright ${
                compact ? "py-2" : "py-3"
              }`}
            />
          </div>
          <div>
            <label htmlFor={messageId} className="mb-1.5 block text-xs tracking-wide text-muted uppercase">
              Message
            </label>
            <textarea
              id={messageId}
              name="message"
              required
              rows={compact ? 3 : 5}
              className={`w-full border border-line bg-steel-800 px-3 text-sm text-foreground outline-none transition focus:border-brand-bright ${
                compact ? "resize-none py-2" : "resize-y py-3"
              }`}
            />
          </div>
          <MagneticButton
            type="submit"
            className={`inline-flex bg-brand-bright text-sm font-semibold tracking-wide text-steel-900 transition hover:bg-[#4db0df] ${
              compact ? "px-5 py-2" : "px-6 py-3"
            }`}
          >
            Submit
          </MagneticButton>
        </form>
      )}

      <div className={compact ? "space-y-4" : "space-y-8"}>
        <div>
          <h3 className={`font-display font-semibold text-foreground ${compact ? "text-lg" : "text-xl"}`}>
            {contact.corporate.title}
          </h3>
          <ul className={`space-y-1 text-sm text-muted ${compact ? "mt-2" : "mt-3"}`}>
            {contact.corporate.lines.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>

        <div className={`border-t border-line ${compact ? "pt-4" : "pt-8"}`}>
          <div className={`relative mb-3 ${compact ? "h-9 w-24" : "h-12 w-28"}`}>
            <Image
              src={contact.primeRebar.logo}
              alt="Prime Rebar LLC"
              fill
              className="object-contain object-left"
            />
          </div>
          <ul className="space-y-1 text-sm text-muted">
            {contact.primeRebar.lines.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>

        <div className={`border-t border-line ${compact ? "pt-4" : "pt-8"}`}>
          <p className="text-xs font-semibold tracking-[0.22em] text-brand-bright uppercase">
            {contact.subsidiariesTitle}
          </p>
          <div className={`grid grid-cols-2 gap-2 ${compact ? "mt-3 sm:grid-cols-4" : "mt-5 gap-4"}`}>
            {contact.subsidiaries.map((sub) => (
              <div
                key={sub.name}
                className={`flex flex-col items-center border border-line bg-white/95 ${
                  compact ? "gap-1 p-2" : "gap-2 p-4"
                }`}
              >
                <div className={`relative w-full ${compact ? "h-9" : "h-14"}`}>
                  <Image src={sub.logo} alt={sub.name} fill className="object-contain" />
                </div>
                <p className="text-center text-[10px] font-medium text-steel-900 sm:text-xs">{sub.name}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

