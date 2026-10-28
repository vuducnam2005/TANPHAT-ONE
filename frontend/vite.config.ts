import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

const odooOrigin = process.env.TP_ODOO_ORIGIN ?? 'http://127.0.0.1:18069';

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  if (command === 'build' && !env.VITE_ODOO_DATABASE?.trim()) {
    throw new Error('Set VITE_ODOO_DATABASE to the target Odoo database before building. See .env.example.');
  }
  return {
    base: '/work/',
    plugins: [react()],
    server: {
      host: '127.0.0.1',
      port: 4173,
      strictPort: true,
      proxy: {
        '/api': {
          target: odooOrigin,
          changeOrigin: true,
          configure: (proxy) => {
            // changeOrigin points Host at Odoo; give same-origin dev requests the
            // matching Origin so the API write guard (Origin = Host) accepts them.
            proxy.on('proxyReq', (proxyReq, req) => {
              const origin = req.headers.origin;
              if (origin && new URL(origin).host === req.headers.host) proxyReq.setHeader('origin', odooOrigin);
            });
          },
        },
        '/web': { target: odooOrigin, changeOrigin: true },
        '/odoo': { target: odooOrigin, changeOrigin: true },
        '/longpolling': { target: odooOrigin, changeOrigin: true, ws: true },
      },
    },
    preview: { host: '127.0.0.1', port: 4173, strictPort: true },
  };
});
