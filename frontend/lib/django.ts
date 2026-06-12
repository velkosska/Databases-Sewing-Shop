/**
 * Django backend URL for browser links (admin, etc.).
 * Set at build time via next.config.ts from DJANGO_API_URL or NEXT_PUBLIC_DJANGO_URL.
 */
export const DJANGO_URL = (
  process.env.NEXT_PUBLIC_DJANGO_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

/** e.g. adminUrl("shop/order/1/change/") */
export function adminUrl(path: string): string {
  return `${DJANGO_URL}/admin/${path.replace(/^\//, "")}`;
}
