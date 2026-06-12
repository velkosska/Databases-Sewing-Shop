"use client";

import { ImagePlaceholder } from "./ImagePlaceholder";
import { useScrollReveal } from "./useScrollReveal";

const GALLERY_ITEMS = [
  "Antes y después — arreglo de cremallera",
  "Antes y después — dobladillo",
  "Antes y después — vestido transformado",
  "Detalle de costura a mano",
  "Prenda a medida terminada",
  "Trabajo de arreglo en el taller",
] as const;

export function Gallery() {
  const { ref, visible } = useScrollReveal<HTMLElement>();

  return (
    <section ref={ref} className={`landing-section landing-section--alt scroll-mt-20 ${visible ? "is-visible" : ""}`}>
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <header className="landing-section-header mb-12 sm:mb-16">
          <h2 className="font-[family-name:var(--font-playfair)] text-3xl sm:text-4xl text-[var(--landing-ink)]">
            Nuestro trabajo
          </h2>
          <span className="landing-underline" aria-hidden />
          <p className="mt-4 max-w-xl text-[var(--landing-muted)]">
            Cada prenda cuenta una historia. Aquí verás ejemplos reales cuando subamos las fotos.
          </p>
        </header>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {GALLERY_ITEMS.map((caption, i) => (
            <div key={caption} className="overflow-hidden rounded-2xl">
              {/* REPLACE: before/after photo */}
              <ImagePlaceholder
                caption={caption}
                alt={`Espacio reservado para foto ${i + 1} del portfolio`}
                aspect="square"
                className="rounded-2xl"
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
