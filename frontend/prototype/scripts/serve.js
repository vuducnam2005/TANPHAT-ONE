import http from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(fileURLToPath(new URL('..', import.meta.url)));
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.json': 'application/json' };
const port = Number(process.env.PORT || 4173);
const server = http.createServer(async (request, response) => {
    try {
        const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
        if (pathname === '/favicon.ico') { response.writeHead(204); response.end(); return; }
        const file = path.resolve(root, `.${pathname === '/' ? '/index.html' : pathname}`);
        if (!file.startsWith(root + path.sep) || !types[path.extname(file)]) {
            response.writeHead(404); response.end('Not found'); return;
        }
        const content = await readFile(file);
        response.writeHead(200, { 'Content-Type': `${types[path.extname(file)]}; charset=utf-8`, 'Cache-Control': 'no-store' });
        response.end(request.method === 'HEAD' ? undefined : content);
    } catch {
        response.writeHead(404); response.end('Not found');
    }
});
server.listen(port, '127.0.0.1', () => process.stdout.write(`Tan Phat frontend: http://127.0.0.1:${port}\n`));
