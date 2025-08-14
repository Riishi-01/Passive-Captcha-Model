import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5700,
    proxy: {
      '/admin': {
        target: 'http://localhost:5600',
        changeOrigin: true,
        secure: false,
      },
      '/api': {
        target: 'http://localhost:5600',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'dist',
  },
})
