/** @type {import('next').NextConfig} */
const nextConfig = {
  // The standalone output holds only the files that the server needs.
  output: "standalone",
  // `next dev` and `next build` both write here. A build during a dev run would
  // overwrite the files that the dev server is serving, so they use separate folders.
  distDir: process.env.NEXT_DIST_DIR ?? ".next",
};

export default nextConfig;
