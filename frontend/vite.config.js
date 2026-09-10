import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

const DEV_SERVER_PORT = 5173;

// One entry for every Django page. Vite emits a manifest that the {% vite_asset %}
// template tag turns into <script>/<link> tags; built assets are served from STATIC_URL.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/static/' : '/',
  plugins: [react(), tailwindcss()],
  build: {
    manifest: true,
    modulePreload: { polyfill: false },
    rollupOptions: { input: 'src/main.jsx' },
  },
  server: {
    port: DEV_SERVER_PORT,
    strictPort: true,
    origin: `http://localhost:${DEV_SERVER_PORT}`,
    cors: true,
  },
}));
