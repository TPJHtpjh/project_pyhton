import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// export default defineConfig({
//   plugins: [react()],
//   base: '/',
// })

// import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    plugins: [react()],
    base: '/',
    proxy: {
      '/api': {
        target: 'http://localhost:8001', // 后端地址
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api/, '/api'), // 保持原路径
      },
    },
  },
});
