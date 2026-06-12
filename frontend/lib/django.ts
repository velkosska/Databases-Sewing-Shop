/**
 * Base URL for the Django backend.
 * - Server-side (SSR/API routes): DJANGO_API_URL (private Railway URL)
 * - Client-side (browser links): NEXT_PUBLIC_DJANGO_URL (public Railway URL)
 *
 * Set NEXT_PUBLIC_DJANGO_URL on the costuras-de-paqui Railway service:
 *   https://databases-sewing-shop-production.up.railway.app
 */
const djangoBase =
  (typeof window === "undefined"
    ? process.env.DJANGO_API_URL
    : process.env.NEXT_PUBLIC_DJANGO_URL) ?? "http://127.0.0.1:8000";

export const DJANGO_URL = djangoBase.replace(/\/$/, "");

/** Build an absolute URL to the Django admin, e.g. adminUrl("shop/order/1/change/") */
export function adminUrl(path: string): string {
  return `${DJANGO_URL}/admin/${path.replace(/^\//, "")}`;
}
