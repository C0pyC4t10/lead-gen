import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://lead-gen-api-nine.vercel.app/api/:path*",
      },
    ];
  },
  async redirects() {
    return [
      {
        source: "/",
        destination: "/leads.html",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
