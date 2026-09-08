import { resolve } from 'node:path';

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

const DEV_SERVER_PORT = 5173;

// Every Django page mounts one React entry. Vite emits a manifest that the
// {% vite_asset %} template tag turns into <script>/<link> tags. Built assets are
// served by Django from STATIC_URL; the dev server serves them from its own root.
export default defineConfig(({ command }) => ({
  root: import.meta.dirname,
  base: command === 'build' ? '/static/' : '/',
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': resolve(import.meta.dirname, 'src') },
  },
  build: {
    manifest: true,
    outDir: 'dist',
    emptyOutDir: true,
    modulePreload: { polyfill: false },
    rollupOptions: {
      input: {
        login: resolve(import.meta.dirname, 'src/entries/login.jsx'),
        signup: resolve(import.meta.dirname, 'src/entries/signup.jsx'),
        legal: resolve(import.meta.dirname, 'src/entries/legal.jsx'),
        'manager-shifts': resolve(import.meta.dirname, 'src/entries/manager-shifts.jsx'),
        'manager-employees': resolve(import.meta.dirname, 'src/entries/manager-employees.jsx'),
        'employee-shifts': resolve(import.meta.dirname, 'src/entries/employee-shifts.jsx'),
      },
    },
  },
  server: {
    port: DEV_SERVER_PORT,
    strictPort: true,
    origin: `http://localhost:${DEV_SERVER_PORT}`,
    cors: true,
  },
}));
