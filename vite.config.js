import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// While developing, send /api requests to the Python backend on port 8000
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
