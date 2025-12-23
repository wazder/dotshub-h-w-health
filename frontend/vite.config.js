import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    
    // Development server configuration
    server: {
        port: 5173,
        host: true,
        
        // API Proxy - Solves CORS issues in development
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false,
                // Log on error
                configure: (proxy, _options) => {
                    proxy.on('error', (err, _req, _res) => {
                        console.log('🔴 Proxy error:', err);
                    });
                    proxy.on('proxyReq', (_proxyReq, req, _res) => {
                        console.log('🔵 Proxying:', req.method, req.url);
                    });
                    proxy.on('proxyRes', (proxyRes, req, _res) => {
                        console.log('🟢 Response:', proxyRes.statusCode, req.url);
                    });
                }
            }
        }
    },
    
    // Build configuration
    build: {
        outDir: 'dist',
        sourcemap: true
    },
    
    // Environment variables prefix
    envPrefix: 'VITE_'
})
