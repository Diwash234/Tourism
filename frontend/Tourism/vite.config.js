import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import path from 'node:path'

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
const siteMetadata = (siteUrl) => {
  // Vite invokes hooks with a rollup context, not the plugin object, so shared
  // state has to live in this closure rather than on `this`.
  let outDir = null
  const base = (siteUrl || '').trim().replace(/\/+$/, '')
  const configured = /^https:\/\/[^\s"'<>]+$/.test(base)

  return {
    name: 'site-metadata',
    configResolved(resolved) {
      outDir = resolved.build.outDir
    },
    transformIndexHtml(html) {
      if (!configured) return html
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

    // robots.txt and sitemap.xml ship from public/ verbatim, so they cannot go
    // through transformIndexHtml. Both are stored with site-relative URLs (the
    // source must never hardcode a domain), but sitemaps.org requires <loc> to
    // be an absolute URL and robots.txt expects an absolute Sitemap: directive
    // -- relative values can cause the whole sitemap to be ignored. Rewrite
    // them at build time from the same VITE_SITE_URL that drives
    // canonical/og/JSON-LD, so all four stay consistent.
    closeBundle() {
      if (!configured || !outDir) return
      const out = path.resolve(outDir)

      const sitemap = path.join(out, 'sitemap.xml')
      if (existsSync(sitemap)) {
        writeFileSync(
          sitemap,
          readFileSync(sitemap, 'utf8').replace(/<loc>\/(?![/])/g, `<loc>${base}/`),
        )
      }

      const robots = path.join(out, 'robots.txt')
      if (existsSync(robots)) {
        writeFileSync(
          robots,
          readFileSync(robots, 'utf8').replace(/^Sitemap:\s*\//gm, `Sitemap: ${base}/`),
        )
      }
    },
  }
}

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
  base: '/static/',
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
    include: ['react', 'react-dom', 'react/jsx-runtime', 'react-icons'],
    force: true,
  },
  build: {
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      output: {
        manualChunks,
        assetFileNames: 'assets/[name]-[hash][extname]',
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
      },
    },
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
