"use client";

import Link from "next/link";
import { ADDRESS, EMAIL, EMAIL_HREF, PHONE_DISPLAY, PHONE_HREF, WHATSAPP_URL } from "./constants";
import { WhatsAppIcon } from "./icons";
import { useScrollReveal } from "./useScrollReveal";

interface ContactCTAProps {
  onOrderClick: () => void;
}

export function ContactCTA({ onOrderClick }: ContactCTAProps) {
  const { ref, visible } = useScrollReveal<HTMLElement>();

  return (
    <section
      id="contacto"
      ref={ref}
      className={`landing-section landing-cta-band scroll-mt-20 ${visible ? "is-visible" : ""}`}
    >
      <div className="mx-auto max-w-3xl px-5 sm:px-8 text-center">
        <h2 className="font-[family-name:var(--font-playfair)] text-3xl sm:text-4xl text-[var(--landing-ink)]">
          ¿Lista para empezar?
        </h2>
        <p className="mt-4 text-[var(--landing-muted)] leading-relaxed">
          Pide tu presupuesto sin compromiso. Te respondemos en menos de 24 horas.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button type="button" onClick={onOrderClick} className="landing-btn landing-btn--primary min-h-12 w-full sm:w-auto px-10">
            Hacer pedido
          </button>
          <a
            href={WHATSAPP_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="landing-btn landing-btn--outline min-h-12 w-full sm:w-auto px-8 inline-flex items-center justify-center gap-2"
          >
            <WhatsAppIcon className="w-5 h-5 text-[#25D366]" />
            WhatsApp
          </a>
        </div>

        <p className="mt-8 text-sm text-[var(--landing-muted)]">O llámanos:</p>
        <a href={PHONE_HREF} className="mt-1 inline-block text-xl font-semibold text-[var(--landing-accent-deep)] hover:underline">
          {PHONE_DISPLAY}
        </a>

        <p className="mt-8 text-sm text-[var(--landing-muted)]">{ADDRESS}</p>
        <a href={EMAIL_HREF} className="mt-1 inline-block text-sm text-[var(--landing-muted)] hover:text-[var(--landing-accent-deep)]">
          {EMAIL}
        </a>

        <p className="mt-6 text-xs text-[var(--landing-muted)]">
          O rellena el{" "}
          <Link href="/presupuesto" className="underline underline-offset-2 hover:text-[var(--landing-ink)]">
            formulario de pedido online
          </Link>
          .
        </p>
      </div>
    </section>
  );
}
