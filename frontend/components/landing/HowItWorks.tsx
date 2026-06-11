"use client";

import { BagStepIcon, ChatIcon, PhoneStepIcon, SparkleIcon } from "./icons";
import { useScrollReveal } from "./useScrollReveal";

const STEPS = [
  {
    number: "1",
    title: "Cuéntanos qué necesitas",
    description: "Escríbenos por WhatsApp o usa el botón de pedido. Te damos precio orientativo.",
    icon: ChatIcon,
  },
  {
    number: "2",
    title: "Te llamamos para confirmar",
    description: "Repasamos detalles y reservamos tu hueco en el taller.",
    icon: PhoneStepIcon,
  },
  {
    number: "3",
    title: "Trae tu prenda",
    description: "Nos entregas la ropa en el taller y acordamos fecha de recogida.",
    icon: BagStepIcon,
  },
  {
    number: "4",
    title: "Recógela como nueva",
    description: "Te avisamos cuando esté lista. Sales con tu prenda renovada.",
    icon: SparkleIcon,
  },
] as const;

export function HowItWorks() {
  const { ref, visible } = useScrollReveal<HTMLElement>();

  return (
    <section
      id="como-funciona"
      ref={ref}
      className={`landing-section landing-section--alt scroll-mt-20 ${visible ? "is-visible" : ""}`}
    >
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <header className="text-center mb-10 sm:mb-14">
          <h2 className="font-[family-name:var(--font-playfair)] text-3xl sm:text-4xl text-[var(--landing-ink)]">
            Cómo funciona
          </h2>
          <p className="mt-3 text-[var(--landing-muted)]">En 60 segundos — cuatro pasos sencillos</p>
        </header>

        <ol className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map(({ number, title, description, icon: Icon }) => (
            <li key={number} className="landing-feature-card p-6 flex flex-col">
              <div className="flex items-center gap-3 mb-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--landing-accent-deep)] text-white text-lg font-bold">
                  {number}
                </span>
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--landing-accent-soft)] text-[var(--landing-accent-deep)]">
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <h3 className="font-semibold text-[var(--landing-ink)]">{title}</h3>
              <p className="mt-2 text-sm text-[var(--landing-muted)] leading-relaxed flex-1">{description}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
