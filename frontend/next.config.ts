import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        // Proxy only the JSON API — admin is opened directly on :8000
        source: "/api/:path*",
        destination: `${process.env.DJANGO_INTERNAL_URL ?? "http://127.0.0.1:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
