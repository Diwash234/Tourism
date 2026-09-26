import { defineConfig, loadEnv } from 'vite'
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

// Deployment-safe SEO metadata. The site must never claim another domain
// (the old template pointed canonical/og:url at nepaltourism.gov.np, which
// implies an official government site). When VITE_SITE_URL is provided at
// build time we inject absolute canonical/og:url/JSON-LD for the home
// document; otherwise nothing is injected and useSeo() derives canonical URLs
// from window.location.origin at runtime.
const siteMetadata = (siteUrl) => ({
  name: 'site-metadata',
  transformIndexHtml(html) {
    const base = (siteUrl || '').trim().replace(/\/+$/, '')
    if (!/^https:\/\/[^\s"'<>]+$/.test(base)) return html
    const jsonLd = {
      '@context': 'https://schema.org',
      '@graph': [
        { '@type': 'Organization', '@id': `${base}/#organization`, name: 'Nepal Yatra', url: `${base}/`, logo: `${base}/favicon.svg` },
        {
          '@type': 'WebSite', '@id': `${base}/#website`, url: `${base}/`, name: 'Nepal Yatra',
          publisher: { '@id': `${base}/#organization` },
          potentialAction: { '@type': 'SearchAction', target: `${base}/destinations?q={search_term_string}`, 'query-input': 'required name=search_term_string' },
        },
      ],
    }
    return {
      html,
      tags: [
        { tag: 'link', attrs: { rel: 'canonical', href: `${base}/` }, injectTo: 'head' },
        { tag: 'meta', attrs: { property: 'og:url', content: `${base}/` }, injectTo: 'head' },
        { tag: 'meta', attrs: { name: 'twitter:url', content: `${base}/` }, injectTo: 'head' },
        { tag: 'script', attrs: { type: 'application/ld+json' }, children: JSON.stringify(jsonLd), injectTo: 'head' },
      ],
    }
  },
})

// Split heavy vendor libraries into their own cacheable chunks.
const manualChunks = (id) => {
  if (!id.includes("node_modules")) return undefined
  if (id.includes("leaflet") || id.includes("react-leaflet")) return "map"
  if (id.includes("chart.js") || id.includes("react-chartjs-2")) return "charts"
  if (id.includes("framer-motion") || id.includes("gsap")) return "motion"
  if (id.includes("react-icons") || id.includes("lucide-react")) return "icons"
  return undefined
}

export default defineConfig(({ mode }) => ({
  plugins: [react(), noStaleReactChunks, siteMetadata(loadEnv(mode, process.cwd(), 'VITE_').VITE_SITE_URL)],
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
      '/robots.txt': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/sitemap.xml': { target: 'http://127.0.0.1:8000', changeOrigin: true },
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
      '/robots.txt': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/sitemap.xml': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
}))
