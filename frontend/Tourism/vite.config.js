import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const noStaleReactChunks = {
  name: 'no-stale-react-chunks',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      // Arena previews can retain an old optimized React chunk across a Vite
      // restart, pairing it with a new react-dom chunk and nulling the hook
      // dispatcher. Never cache dev JS/prebundle responses.
      if (req.url?.includes('/node_modules/.vite/') || req.url?.match(/\.(js|jsx)(\?|$)/)) {
        res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate')
        res.setHeader('Pragma', 'no-cache')
        res.setHeader('Expires', '0')
      }
      next()
    })
  },
}

// Split heavy vendor libraries into their own cacheable chunks. Without this
// everything (leaflet, chart.js, framer-motion, gsap, react-icons) lands in
// one ~2 MB bundle that must download before the first paint — a big part of
// "the site feels slow" on mobile. With manual chunks the initial page loads
// a small core + one parallel chunk per feature area, and revisits hit the
// browser cache for the big libraries.
const manualChunks = (id) => {
  if (!id.includes("node_modules")) return undefined
  if (id.includes("leaflet") || id.includes("react-leaflet")) return "map"
  if (id.includes("chart.js") || id.includes("react-chartjs-2")) return "charts"
  if (id.includes("framer-motion") || id.includes("gsap")) return "motion"
  if (id.includes("react-icons") || id.includes("lucide-react")) return "icons"
  if (
    id.includes("react-router") || id.includes("react-dom") ||
    id.includes("/react/") || id.includes("scheduler")
  ) return "react"
  return "vendor"
}

export default defineConfig({
  plugins: [react(), noStaleReactChunks],
  build: {
    rollupOptions: {
      output: {
        manualChunks,
      },
    },
  },
  // Prevent invalid-hook-call / null React dispatcher errors when linked
  // packages or Vite dependency optimization resolve React more than once.
  resolve: {
    dedupe: ['react', 'react-dom'],
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react/jsx-runtime', 'react-icons/fi', 'react-icons/bs'],
    force: true,
  },
  server: {
    host: '0.0.0.0',
    hmr: false,
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/ws': { target: 'ws://127.0.0.1:8000', ws: true },
      '/django-admin': { target: 'http://127.0.0.1:8000', changeOrigin: true, followRedirects: true, rewrite: (path) => path.replace(/^\/django-admin/, '/admin') },
      '/media': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/static': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  // Arena's stable sandbox uses the production bundle. This avoids any
  // possibility of old/new HMR React chunks sharing a page.
  preview: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/ws': { target: 'ws://127.0.0.1:8000', ws: true },
      '/django-admin': { target: 'http://127.0.0.1:8000', changeOrigin: true, followRedirects: true, rewrite: (path) => path.replace(/^\/django-admin/, '/admin') },
      '/media': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/static': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
