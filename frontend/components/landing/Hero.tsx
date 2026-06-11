"use client";

import Image from "next/image";
import { BUSINESS_NAME, HERO_SUBTITLE, TAGLINE } from "./constants";
import { scrollToId } from "./scroll";
import paquiHero from "@/app/(landing)/shop_large_Costuras_de_Paqui2.jpg";

const NEED_OPTIONS = [
  { label: "Arreglo", target: "servicios" },
  { label: "Confección", target: "servicios" },
  { label: "Tintorería", target: "servicios" },
] as const;

interface HeroProps {
  onOrderClick: () => void;
}

export function Hero({ onOrderClick }: HeroProps) {
  return (
    <section className="landing-hero relative pt-24 pb-16 sm:pt-28 sm:pb-20">
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          {/* Copy */}
          <div className="landing-hero-content text-center lg:text-left">
            <p className="text-sm font-semibold uppercase tracking-widest text-[var(--landing-accent)]">
              Arreglos y confecciones · Madrid
            </p>
            <h1 className="mt-4 font-[family-name:var(--font-playfair)] text-4xl sm:text-5xl lg:text-6xl font-semibold text-[var(--landing-ink)] leading-[1.1]">
              Bienvenida a{" "}
              <span className="text-[var(--landing-accent-deep)]">{BUSINESS_NAME}</span>
            </h1>
            <p className="mt-5 text-lg sm:text-xl text-[var(--landing-muted)] leading-relaxed max-w-xl mx-auto lg:mx-0">
              {TAGLINE}
            </p>
            <p className="mt-2 text-base text-[var(--landing-muted)] italic">{HERO_SUBTITLE}</p>

            <div className="landing-order-card mt-10 mx-auto lg:mx-0 max-w-md text-left">
              <p className="text-sm font-semibold text-[var(--landing-ink)] mb-3">¿Qué necesitas?</p>
              <div className="flex flex-wrap gap-2 mb-5">
                {NEED_OPTIONS.map(({ label, target }) => (
                  <button
                    key={label}
                    type="button"
                    onClick={() => scrollToId(target)}
                    className="landing-chip min-h-12 px-4 rounded-xl text-sm font-medium"
                  >
                    {label}
                  </button>
                ))}
              </div>
              <button
                type="button"
                onClick={onOrderClick}
                className="landing-btn landing-btn--primary w-full min-h-12 text-base"
              >
                Hacer pedido
              </button>
              <p className="mt-3 text-xs text-center text-[var(--landing-muted)]">
                Sin compromiso · Te respondemos en menos de 24 horas
              </p>
            </div>
          </div>

          {/* Hero photo — Paqui at the stall */}
          <div className="relative">
            <div
              data-slot="hero-bg"
              className="landing-hero-visual relative rounded-3xl overflow-hidden aspect-[4/5] sm:aspect-[5/6] max-h-[520px] mx-auto lg:max-h-none shadow-lg"
            >
              <Image
                src={paquiHero}
                alt="Paqui en su puesto de Costuras de Paqui en el mercado de San Enrique, Madrid"
                fill
                className="object-cover object-center"
                sizes="(max-width: 1024px) 100vw, 560px"
                priority
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
