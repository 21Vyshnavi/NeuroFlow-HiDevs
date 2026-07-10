/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone output bundles only the required files for a minimal Docker image
  output: 'standalone',

  async rewrites() {
    return [
      {
        // In production, Nginx proxies /api/* → api service directly.
        // In dev, Next.js proxies to localhost:8000.
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL
          ? `${process.env.NEXT_PUBLIC_API_URL}/:path*`
          : 'http://localhost:8000/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
