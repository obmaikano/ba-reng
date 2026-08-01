import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  base: process.env.VITE_BASE_URL || '/',
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // In Docker Compose the backend is reachable by service name; when
      // running the Vite dev server on the host, localhost is correct.
      '/api': process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
    },
  },
});
