import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const DJANGO_BACKEND =
  process.env.VITE_DJANGO_ORIGIN || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,
    open: true,

    proxy: {
      // Django API
      '/api': {
        target: DJANGO_BACKEND,
        changeOrigin: true,
      },

      // Django static files
      '/static': {
        target: DJANGO_BACKEND,
        changeOrigin: true,
      },

      // Django media files
      '/media': {
        target: DJANGO_BACKEND,
        changeOrigin: true,
      },
    },
  },
})
