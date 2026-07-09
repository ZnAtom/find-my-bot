import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://172.17.0.1:8000',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://172.17.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
