import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { host: '0.0.0.0', port: 5173, strictPort: true },
  preview: { host: '0.0.0.0', port: 3000, strictPort: true },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/react') || id.includes('node_modules/scheduler')) return 'react-vendor'
          if (id.includes('node_modules/recharts') || id.includes('node_modules/d3-')) return 'charts-vendor'
          if (id.includes('node_modules/lucide-react')) return 'icons-vendor'
        },
      },
    },
  },
})
