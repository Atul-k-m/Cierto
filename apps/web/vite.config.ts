import react from '@vitejs/plugin-react'
import { resolve } from 'node:path'
import { defineConfig } from 'vite'

// The product site and one page per host replica. `npm run build` also prerenders every site route
// (vite build --ssr + scripts/prerender.mjs); `python -m wismo serve` serves the result and the API on one port.
export default defineConfig(({ isSsrBuild }) => ({
  plugins: [react()],
  server: { port: 5173, fs: { allow: ['../..'] }, proxy: { '/v1': 'http://127.0.0.1:8787' } },
  preview: { port: 4173, proxy: { '/v1': 'http://127.0.0.1:8787' } },
  build: isSsrBuild ? { outDir: 'dist-ssr', emptyOutDir: true } : {
    manifest: true, // read by scripts/prerender.mjs to preload each page's own chunks
    rollupOptions: {
      input: {
        site: resolve(import.meta.dirname, 'index.html'),
        smytten: resolve(import.meta.dirname, 'hosts/smytten.html'),
        zomato: resolve(import.meta.dirname, 'hosts/zomato.html'),
        swish: resolve(import.meta.dirname, 'hosts/swish.html'),
      },
    },
  },
}))
