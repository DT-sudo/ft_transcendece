import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// One entry for every Django page. Vite emits a manifest that the {% vite_asset %}
// template tag turns into <script>/<link> tags; built assets are served from STATIC_URL.
export default defineConfig({
  base: '/static/',
  plugins: [react(), tailwindcss()],
  build: {
    manifest: true,
    modulePreload: { polyfill: false },
    rollupOptions: { input: 'src/main.jsx' },
  },
});
