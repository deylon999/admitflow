import { fileURLToPath } from 'node:url';
const sourceRoot = fileURLToPath(new URL('../../admitflow-frontend-v3-main/', import.meta.url));

// Serve the actual sibling React project. Its files and node_modules stay read only.
export default {
  root: sourceRoot,
  build: { outDir: fileURLToPath(new URL('./node_modules/.cache/reference-v3-dist', import.meta.url)), emptyOutDir: true },
  preview: { host: '127.0.0.1', port: 5300, strictPort: true },
  cacheDir: fileURLToPath(new URL('./node_modules/.cache/reference-v3', import.meta.url)),
  server: { host: '127.0.0.1', port: 5300, strictPort: true },
};
