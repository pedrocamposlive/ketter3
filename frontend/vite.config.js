import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/transfers': {
        target: 'http://api:8000',
        changeOrigin: true
      },
      '/volumes': {
        target: 'http://api:8000',
        changeOrigin: true
      },
      '/health': {
        target: 'http://api:8000',
        changeOrigin: true
      },
      '/status': {
        target: 'http://api:8000',
        changeOrigin: true
      }
    }
  }
})
