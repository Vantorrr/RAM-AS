import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Для Railway используем обычный сервер, не static export
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
