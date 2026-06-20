import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env from the root directory
  const env = loadEnv(mode, '../', '')
  const port = parseInt(env.VITE_FRONTEND_PORT || '5173')
  
  return {
    plugins: [react()],
    envDir: '../', // Expose root .env variables prefixed with VITE_ to the client
    server: {
      port: port,
      strictPort: true, // Fail if port is already in use instead of trying the next one
    }
  }
})
