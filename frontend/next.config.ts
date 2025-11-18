import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  output: 'standalone', // For Docker deployment
  // Disable ESLint during builds (optional)
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
