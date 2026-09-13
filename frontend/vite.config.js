import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// One entry serves every page. render_app() reads the emitted manifest to link the
// hashed bundle; built assets are served from STATIC_URL.
export default defineConfig({
  base: '/static/',
  plugins: [react(), tailwindcss()],
  build: {
    manifest: true,
    modulePreload: { polyfill: false },
    rollupOptions: { input: 'src/main.jsx' },
  },
});
