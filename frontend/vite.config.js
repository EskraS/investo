import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Port pinned to 5173 — matches the CORS origin in backend/main.py.
// Two terminals during dev: uvicorn in backend/, `npm run dev` here.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
})
