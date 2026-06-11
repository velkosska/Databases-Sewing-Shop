"use client";

import { SERVICES } from "./constants";
import { ScissorsIcon } from "./icons";
import { useScrollReveal } from "./useScrollReveal";

export function Services() {
  const { ref, visible } = useScrollReveal<HTMLElement>();

  return (
    <section
      id="servicios"
      ref={ref}
      className={`landing-section scroll-mt-20 ${visible ? "is-visible" : ""}`}
    >
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <header className="text-center mb-10 sm:mb-14">
          <h2 className="font-[family-name:var(--font-playfair)] text-3xl sm:text-4xl text-[var(--landing-ink)]">
            Nuestros servicios
          </h2>
          <p className="mt-3 text-[var(--landing-muted)] max-w-2xl mx-auto">
            Arreglos, confección, hogar, motoristas y tintorería — todo en un mismo taller de confianza.
          </p>
        </header>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {SERVICES.map(({ title, description }) => (
            <article key={title} className="landing-feature-card p-6 sm:p-7">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--landing-accent-soft)] text-[var(--landing-accent-deep)]">
                <ScissorsIcon className="w-6 h-6" />
              </div>
              <h3 className="font-[family-name:var(--font-playfair)] text-lg text-[var(--landing-ink)]">{title}</h3>
              <p className="mt-2 text-sm text-[var(--landing-muted)] leading-relaxed">{description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
