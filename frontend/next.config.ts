import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Only use static export for production builds (S3 deployment)
  ...(process.env.NODE_ENV === 'production' && {
    output: 'export',
    trailingSlash: true,
    images: {
      unoptimized: true
    }
  }),
  // Development settings
  ...(process.env.NODE_ENV === 'development' && {
    images: {
      domains: ['localhost']
    }
  })
};

export default nextConfig;
