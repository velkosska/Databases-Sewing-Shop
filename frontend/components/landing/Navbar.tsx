"use client";

import { useEffect, useState } from "react";
import { BUSINESS_NAME } from "./constants";
import { scrollToId } from "./scroll";
import { useNavbarSolid } from "./useNavbarSolid";

const NAV_LINKS = [
  { id: "servicios", label: "Servicios" },
  { id: "como-funciona", label: "Cómo funciona" },
  { id: "sobre-paqui", label: "Sobre Paqui" },
  { id: "contacto", label: "Contacto" },
] as const;

interface LandingNavbarProps {
  onOrderClick: () => void;
}

export function LandingNavbar({ onOrderClick }: LandingNavbarProps) {
  const scrolled = useNavbarSolid(24);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  function goTo(id: string) {
    setMenuOpen(false);
    scrollToId(id);
  }

  function handleOrder() {
    setMenuOpen(false);
    onOrderClick();
  }

  return (
    <>
      <header
        className={`landing-navbar fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
          scrolled ? "landing-navbar--scrolled shadow-sm" : ""
        }`}
      >
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-5 sm:px-8">
          <a
            href="#"
            className="font-[family-name:var(--font-playfair)] text-lg sm:text-xl font-semibold text-[var(--landing-ink)] shrink-0"
            onClick={(e) => {
              e.preventDefault();
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          >
            {BUSINESS_NAME}
          </a>

          <nav className="hidden lg:flex items-center gap-1" aria-label="Principal">
            {NAV_LINKS.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                onClick={() => goTo(id)}
                className="landing-nav-link px-3 py-2 text-sm font-medium text-[var(--landing-muted)] rounded-lg hover:text-[var(--landing-ink)] hover:bg-[var(--landing-surface)] transition"
              >
                {label}
              </button>
            ))}
          </nav>

          <button
            type="button"
            onClick={handleOrder}
            className="landing-btn landing-btn--primary hidden sm:inline-flex min-h-12 px-6"
          >
            Hacer pedido
          </button>

          <button
            type="button"
            className="lg:hidden flex h-12 w-12 items-center justify-center rounded-xl text-[var(--landing-ink)] hover:bg-[var(--landing-surface)]"
            aria-expanded={menuOpen}
            aria-label={menuOpen ? "Cerrar menú" : "Abrir menú"}
            onClick={() => setMenuOpen((o) => !o)}
          >
            {menuOpen ? (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24" aria-hidden>
                <path strokeLinecap="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24" aria-hidden>
                <path strokeLinecap="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>
      </header>

      <div
        className={`fixed inset-0 z-40 flex flex-col bg-white pt-20 px-6 transition-all duration-300 lg:hidden ${
          menuOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
        aria-hidden={!menuOpen}
      >
        <nav className="flex flex-col gap-1">
          {NAV_LINKS.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              onClick={() => goTo(id)}
              className="rounded-xl px-4 py-4 text-left text-lg font-medium text-[var(--landing-ink)] hover:bg-[var(--landing-surface)]"
            >
              {label}
            </button>
          ))}
        </nav>
        <button type="button" onClick={handleOrder} className="landing-btn landing-btn--primary mt-8 min-h-12 w-full">
          Hacer pedido
        </button>
      </div>
    </>
  );
}
