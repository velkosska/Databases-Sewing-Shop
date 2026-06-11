import type { NextConfig } from "next";

const djangoApiOrigin =
  process.env.DJANGO_API_URL?.replace(/\/$/, "") ||
  process.env.API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
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
