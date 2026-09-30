// The React wrapper: dist/react.mjs (ESM). React stays external; the wrapper takes a client from Cierto.init().
import { resolve } from 'node:path'
import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    outDir: 'dist',
    emptyOutDir: false,
    sourcemap: true,
    target: 'es2022',
    lib: { entry: resolve(import.meta.dirname, 'src/react.tsx'), formats: ['es'], fileName: () => 'react.mjs' },
    rollupOptions: { external: ['react', 'react/jsx-runtime', 'react-dom'] },
  },
})
