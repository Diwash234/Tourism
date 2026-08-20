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

export default defineConfig({
  plugins: [react(), noStaleReactChunks],
  // Prevent invalid-hook-call / null React dispatcher errors when linked
  // packages or Vite dependency optimization resolve React more than once.
  resolve: {
    dedupe: ['react', 'react-dom'],
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react/jsx-runtime'],
    force: true,
  },
  server: {
    host: '0.0.0.0',
    hmr: false,
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
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
      '/django-admin': { target: 'http://127.0.0.1:8000', changeOrigin: true, followRedirects: true, rewrite: (path) => path.replace(/^\/django-admin/, '/admin') },
      '/media': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/static': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
