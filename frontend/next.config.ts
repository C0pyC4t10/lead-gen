import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://192.168.68.116:8800/api/:path*",
      },
    ];
  },
};

export default nextConfig;
