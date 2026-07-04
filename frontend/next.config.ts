import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://lead-gen-api.fly.dev/api/:path*",
      },
    ];
  },
};

export default nextConfig;
