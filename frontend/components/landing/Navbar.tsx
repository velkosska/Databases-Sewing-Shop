"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
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
  /** Optional override; defaults to /presupuesto or scroll-to-top on order page */
  onOrderClick?: () => void;
}

export function LandingNavbar({ onOrderClick }: LandingNavbarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const isHome = pathname === "/";
  const isOrderPage = pathname === "/presupuesto";
  const scrolled = useNavbarSolid(24);
  const solid = scrolled || !isHome;
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  function closeMenu() {
    setMenuOpen(false);
  }

  function handleNav(sectionId: string) {
    closeMenu();
    if (isHome) {
      scrollToId(sectionId);
      return;
    }
    router.push(`/#${sectionId}`);
  }

  function handleOrder() {
    closeMenu();
    if (isOrderPage) {
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    if (onOrderClick) {
      onOrderClick();
      return;
    }
    router.push("/presupuesto");
  }

  const orderLabel = isOrderPage ? "Arriba" : "Hacer pedido";

  return (
    <>
      <header
        className={`landing-navbar fixed top-0 inset-x-0 z-[60] transition-all duration-300 ${
          solid ? "landing-navbar--scrolled shadow-sm" : ""
        }`}
      >
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4 sm:px-8">
          <Link
            href="/"
            className="font-[family-name:var(--font-playfair)] text-base sm:text-xl font-semibold text-[var(--landing-ink)] shrink-0 min-w-0 truncate"
            onClick={closeMenu}
          >
            {BUSINESS_NAME}
          </Link>

          <nav className="hidden lg:flex items-center gap-1" aria-label="Principal">
            {NAV_LINKS.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                onClick={() => handleNav(id)}
                className="landing-nav-link px-3 py-2 text-sm font-medium text-[var(--landing-muted)] rounded-lg hover:text-[var(--landing-ink)] hover:bg-[var(--landing-surface)] transition"
              >
                {label}
              </button>
            ))}
          </nav>

          <div className="flex items-center gap-2 shrink-0">
            {!isOrderPage && (
              <button
                type="button"
                onClick={handleOrder}
                className="landing-btn landing-btn--primary hidden sm:inline-flex min-h-11 px-4 sm:px-6 text-sm sm:text-base"
              >
                Hacer pedido
              </button>
            )}

            <button
              type="button"
              className="lg:hidden flex h-11 w-11 sm:h-12 sm:w-12 items-center justify-center rounded-xl text-[var(--landing-ink)] hover:bg-[var(--landing-surface)]"
              aria-expanded={menuOpen}
              aria-controls="landing-mobile-menu"
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
        </div>
      </header>

      <div
        id="landing-mobile-menu"
        className={`fixed inset-0 z-[55] flex flex-col bg-white pt-[4.5rem] px-5 pb-8 transition-all duration-300 lg:hidden overflow-y-auto ${
          menuOpen ? "opacity-100 pointer-events-auto visible" : "opacity-0 pointer-events-none invisible"
        }`}
        aria-hidden={!menuOpen}
      >
        <nav className="flex flex-col gap-1" aria-label="Menú móvil">
          <Link
            href="/"
            onClick={closeMenu}
            className="rounded-xl px-4 py-3.5 text-left text-base font-medium text-[var(--landing-ink)] hover:bg-[var(--landing-surface)]"
          >
            Inicio
          </Link>
          {NAV_LINKS.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              onClick={() => handleNav(id)}
              className="rounded-xl px-4 py-3.5 text-left text-base font-medium text-[var(--landing-ink)] hover:bg-[var(--landing-surface)]"
            >
              {label}
            </button>
          ))}
        </nav>
        <button
          type="button"
          onClick={handleOrder}
          className="landing-btn landing-btn--primary mt-6 min-h-12 w-full"
        >
          {orderLabel}
        </button>
      </div>
    </>
  );
}
