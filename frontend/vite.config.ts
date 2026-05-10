import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 11081,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:11080',
        changeOrigin: true,
      },
      '/rss': {
        target: 'http://127.0.0.1:11080',
        changeOrigin: true,
      },
    },
  },
})
