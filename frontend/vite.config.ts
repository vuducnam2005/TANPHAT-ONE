import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const odooOrigin = process.env.TP_ODOO_ORIGIN ?? 'http://127.0.0.1:18069';

export default defineConfig({
  base: '/work/',
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 4173,
    strictPort: true,
    proxy: {
      '/api': { target: odooOrigin, changeOrigin: true },
      '/web': { target: odooOrigin, changeOrigin: true },
      '/odoo': { target: odooOrigin, changeOrigin: true },
      '/longpolling': { target: odooOrigin, changeOrigin: true, ws: true },
    },
  },
  preview: { host: '127.0.0.1', port: 4173, strictPort: true },
});
