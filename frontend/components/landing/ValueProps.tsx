"use client";

import { HangerIcon, NeedleIcon, ScissorsIcon } from "./icons";
import { useScrollReveal } from "./useScrollReveal";

const PROPS = [
  {
    icon: ScissorsIcon,
    title: "Arreglos con cariño",
    description: "Cada prenda se trata como si fuera nuestra. Cremalleras, dobladillos, roturas — lo resolvemos.",
  },
  {
    icon: HangerIcon,
    title: "Variedad de tejidos",
    description: "Textil, pieles, hogar y equipamiento de motorista — un solo taller para muchas necesidades.",
  },
  {
    icon: NeedleIcon,
    title: "Trato personal",
    description: "Taller de barrio en Madrid. Te explicamos el precio antes de empezar y te avisamos cuando esté lista.",
  },
] as const;

export function ValueProps() {
  const { ref, visible } = useScrollReveal<HTMLElement>();

  return (
    <section ref={ref} className={`landing-section landing-section--compact ${visible ? "is-visible" : ""}`}>
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <div className="grid gap-6 md:grid-cols-3">
          {PROPS.map(({ icon: Icon, title, description }) => (
            <article key={title} className="landing-feature-card p-6 sm:p-8">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--landing-accent-soft)] text-[var(--landing-accent-deep)]">
                <Icon />
              </div>
              <h3 className="text-lg font-semibold text-[var(--landing-ink)]">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[var(--landing-muted)]">{description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
