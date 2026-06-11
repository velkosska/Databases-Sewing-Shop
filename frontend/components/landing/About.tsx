"use client";

import { ABOUT_BIO, OPENING_HOURS } from "./constants";
import { ImagePlaceholder } from "./ImagePlaceholder";
import { useScrollReveal } from "./useScrollReveal";

export function About() {
  const { ref, visible } = useScrollReveal<HTMLElement>();

  return (
    <section
      id="sobre-paqui"
      ref={ref}
      className={`landing-section scroll-mt-20 ${visible ? "is-visible" : ""}`}
    >
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <div className="grid items-start gap-12 lg:grid-cols-2 lg:gap-16">
          {/* REPLACE: portrait photo of Paqui or photo of the stall */}
          <ImagePlaceholder
            caption="Foto del puesto en el mercado"
            alt="Espacio reservado para foto del taller o puesto de Paqui"
            aspect="portrait"
            className="mx-auto w-full max-w-sm lg:max-w-none rounded-3xl overflow-hidden"
          />

          <div>
            <h2 className="font-[family-name:var(--font-playfair)] text-3xl sm:text-4xl text-[var(--landing-ink)]">
              Sobre Paqui
            </h2>
            <p className="mt-6 text-[var(--landing-muted)] leading-relaxed">{ABOUT_BIO}</p>

            <div className="mt-10 rounded-2xl border border-[var(--landing-border)] bg-[var(--landing-surface)] p-6">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--landing-ink)]">
                Horario
              </h3>
              <ul className="mt-4 space-y-3">
                {OPENING_HOURS.map(({ days, times }) => (
                  <li key={days} className="flex flex-col sm:flex-row sm:justify-between gap-1 text-sm">
                    <span className="font-medium text-[var(--landing-ink)]">{days}</span>
                    <span className="text-[var(--landing-muted)]">{times}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
