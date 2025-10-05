import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: './postcss.config.cjs',
  },
  server: { 
    port: 3000 
  },
  // Configuration pour Netlify
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser'
  }
})