import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// O navegador fala só com o Vite (porta 5173); o Vite repassa /api para o Django.
// Assim não precisa de CORS, nem no Codespace.
export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
