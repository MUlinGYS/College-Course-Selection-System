import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return

          if (id.includes('element-plus')) {
            return 'element-plus'
          }

          if (id.includes('vue') || id.includes('vue-router')) {
            return 'vue-vendor'
          }
        },
      },
    },
  },
  server: {
    // 让前端访问 `/api/*` 时自动转发到 Django 后端，避免跨域调试成本
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})

