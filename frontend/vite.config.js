import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
//
// VITE_BASE controla o prefixo de assets do build:
// - "/" (default): para deploy direto em mirofish-inteia.vercel.app/
// - "/mirofish/": para sync em pesquisa-eleitoral-df/frontend/public/mirofish/
//   (servido em https://inteia.com.br/mirofish/)
//
// Setar via env: VITE_BASE=/mirofish/ npm run build
const base = process.env.VITE_BASE || '/'
const devPort = Number(process.env.VITE_DEV_PORT || 5173)

export default defineConfig({
  base,
  plugins: [vue()],
  server: {
    port: devPort,
    strictPort: true,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
