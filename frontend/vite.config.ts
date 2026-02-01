import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from "path"
import tailwindcss from "@tailwindcss/vite"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true, // Listen on 0.0.0.0 to be accessible from outside container
    port: 5173,
    strictPort: true, // Exit if port is already in use
    watch: {
      usePolling: true, // Required for hot-reload in Docker volumes
    },
  },
})
