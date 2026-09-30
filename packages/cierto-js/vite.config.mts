// The browser SDK: dist/cierto.js (UMD, global `Cierto`, for a <script> tag) and dist/cierto.mjs (ESM).
// The widget source lives in apps/web/src/widget; it is bundled in, with its icons, so the SDK has no runtime deps.
import { resolve } from 'node:path'
import { defineConfig } from 'vite'

export default defineConfig({
  resolve: { dedupe: ['lucide'] },   // resolve the widget's imports from this package, not apps/web
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,
    target: 'es2022',
    lib: {
      entry: resolve(import.meta.dirname, 'src/index.ts'),
      name: 'Cierto',
      formats: ['es', 'umd'],
      fileName: (format) => (format === 'es' ? 'cierto.mjs' : 'cierto.js'),
    },
  },
})
