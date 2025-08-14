import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor_react: ['react', 'react-dom', 'react-router-dom'],
          vendor_charts: ['recharts'],
          vendor_icons: ['lucide-react']
        }
      }
    }
  },
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
})
