import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },

  // Development server configuration
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5003',
        changeOrigin: true,
        secure: false
      },
      '/admin': {
        target: 'http://localhost:5003',
        changeOrigin: true,
        secure: false
      }
    }
  },

  // Build configuration for production
  build: {
    target: 'esnext',
    minify: 'terser',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          ui: ['@headlessui/vue', '@heroicons/vue', 'lucide-vue-next'],
          charts: ['chart.js', 'vue-chartjs'],
          utils: ['axios', 'date-fns', '@vueuse/core']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },

  // Environment variables
  define: {
    __VUE_PROD_DEVTOOLS__: false,
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false
  },

  // Preview configuration
  preview: {
    port: 4173,
    host: true
  }
}) 