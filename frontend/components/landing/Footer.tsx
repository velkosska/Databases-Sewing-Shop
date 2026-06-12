import Link from "next/link";
import {
  ADDRESS,
  BUSINESS_NAME,
  EMAIL,
  EMAIL_HREF,
  INSTAGRAM_URL,
  OPENING_HOURS,
  PHONE_DISPLAY,
  PHONE_HREF,
  TIKTOK_URL,
  WEBSITE_URL,
} from "./constants";

export function LandingFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="landing-footer border-t border-[var(--landing-border)] bg-white">
      <div className="mx-auto max-w-6xl px-5 py-12 sm:px-8 sm:py-14">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="font-[family-name:var(--font-playfair)] text-xl font-semibold text-[var(--landing-ink)]">
              {BUSINESS_NAME}
            </p>
            <p className="mt-3 text-sm text-[var(--landing-muted)] leading-relaxed">{ADDRESS}</p>
            <a href={PHONE_HREF} className="mt-2 block text-sm text-[var(--landing-accent-deep)] hover:underline">
              {PHONE_DISPLAY}
            </a>
            <a href={EMAIL_HREF} className="mt-1 block text-sm text-[var(--landing-muted)] hover:text-[var(--landing-accent-deep)]">
              {EMAIL}
            </a>
          </div>

          <div>
            <p className="text-sm font-semibold text-[var(--landing-ink)] mb-3">Horario</p>
            <ul className="space-y-2 text-sm text-[var(--landing-muted)]">
              {OPENING_HOURS.map(({ days, times }) => (
                <li key={days}>
                  <span className="font-medium text-[var(--landing-ink)]">{days}:</span> {times}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="text-sm font-semibold text-[var(--landing-ink)] mb-3">Navegación</p>
            <ul className="space-y-2 text-sm text-[var(--landing-muted)]">
              <li><a href="#servicios" className="hover:text-[var(--landing-accent-deep)]">Servicios</a></li>
              <li><a href="#como-funciona" className="hover:text-[var(--landing-accent-deep)]">Cómo funciona</a></li>
              <li><a href="#sobre-paqui" className="hover:text-[var(--landing-accent-deep)]">Sobre Paqui</a></li>
              <li><a href="#contacto" className="hover:text-[var(--landing-accent-deep)]">Contacto</a></li>
            </ul>
          </div>

          <div>
            <p className="text-sm font-semibold text-[var(--landing-ink)] mb-3">Enlaces</p>
            <ul className="space-y-2 text-sm text-[var(--landing-muted)]">
              <li>
                <a href={WEBSITE_URL} target="_blank" rel="noopener noreferrer" className="hover:text-[var(--landing-accent-deep)]">
                  Página de negocio
                </a>
              </li>
              <li>
                <a href={INSTAGRAM_URL} target="_blank" rel="noopener noreferrer" className="hover:text-[var(--landing-accent-deep)]">
                  Instagram
                </a>
              </li>
              <li>
                <a href={TIKTOK_URL} target="_blank" rel="noopener noreferrer" className="hover:text-[var(--landing-accent-deep)]">
                  TikTok
                </a>
              </li>
              <li>
                <Link href="/presupuesto" className="hover:text-[var(--landing-accent-deep)]">
                  Hacer pedido online
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-10 border-t border-[var(--landing-border)] pt-6 text-center text-xs text-[var(--landing-muted)]">
          © {year} {BUSINESS_NAME}. Todos los derechos reservados.
        </div>
      </div>
    </footer>
  );
}
