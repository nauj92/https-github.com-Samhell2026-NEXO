import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Pruebas del frontend (npm test): Vitest + Testing Library sobre jsdom
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
    css: false,
    testTimeout: 30000, // equipos lentos: la primera carga de Intl (es-CO) puede tardar
    hookTimeout: 30000,
  },
})
