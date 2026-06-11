"use client";

import { useScrollReveal } from "./useScrollReveal";

const TRUST_ITEMS = [
  {
    title: "Presupuesto claro",
    description: "Te decimos el precio orientativo antes de coser. Sin sorpresas al recoger.",
  },
  {
    title: "Taller de confianza",
    description: "Años cuidando la ropa de vecinas y clientes de Madrid. Trato cercano, siempre.",
  },
  {
    title: "Respuesta rápida",
    description: "WhatsApp o teléfono. Te contestamos en menos de 24 horas laborables.",
  },
] as const;

export function TrustSection() {
  const { ref, visible } = useScrollReveal<HTMLElement>();

  return (
    <section ref={ref} className={`landing-section landing-section--alt ${visible ? "is-visible" : ""}`}>
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <header className="text-center mb-10 sm:mb-12">
          <h2 className="font-[family-name:var(--font-playfair)] text-2xl sm:text-3xl text-[var(--landing-ink)]">
            Por qué confiar en nosotras
          </h2>
          <p className="mt-3 text-[var(--landing-muted)] max-w-lg mx-auto">
            Simple, honesto y humano — como debe ser un taller de barrio.
          </p>
        </header>
        <div className="grid gap-5 md:grid-cols-3">
          {TRUST_ITEMS.map(({ title, description }) => (
            <div key={title} className="landing-feature-card p-6 border-l-4 border-l-[var(--landing-accent)]">
              <h3 className="font-semibold text-[var(--landing-ink)]">{title}</h3>
              <p className="mt-2 text-sm text-[var(--landing-muted)] leading-relaxed">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
