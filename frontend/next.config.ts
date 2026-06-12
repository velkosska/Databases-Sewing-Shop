import type { NextConfig } from "next";

const djangoApiOrigin =
  process.env.DJANGO_API_URL?.replace(/\/$/, "") ||
  process.env.DJANGO_INTERNAL_URL?.replace(/\/$/, "") ||
  process.env.API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

/** Baked into the client bundle at build time (NEXT_PUBLIC_* must exist at build). */
const publicDjangoUrl =
  process.env.NEXT_PUBLIC_DJANGO_URL?.replace(/\/$/, "") || djangoApiOrigin;

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_DJANGO_URL: publicDjangoUrl,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${djangoApiOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
