import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Убрали output: "export" для Railway
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
