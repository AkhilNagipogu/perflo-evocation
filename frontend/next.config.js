/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.INTERNAL_API_URL 
          ? `${process.env.INTERNAL_API_URL}/api/v1/:path*`
          : 'http://localhost:8000/api/v1/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
