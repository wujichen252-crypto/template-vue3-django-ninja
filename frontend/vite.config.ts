import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig(({ mode }) => {
  const isAnalyze = process.env.ANALYZE === 'true'

  return {
    plugins: [
      vue(),
      // 包分析插件，仅在 ANALYZE=true 时启用
      isAnalyze && visualizer({
        open: true,
        gzipSize: true,
        brotliSize: true,
        filename: 'dist/stats.html'
      })
    ].filter(Boolean),

    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },

    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true
        }
      },
      // 优化开发服务器性能
      hmr: {
        overlay: false // 禁用全屏错误遮罩，提升开发体验
      }
    },

    build: {
      // 启用 CSS 代码分割
      cssCodeSplit: true,

      // 压缩配置
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: true,      // 移除 console.log
          drop_debugger: true,     // 移除 debugger
          pure_funcs: ['console.info', 'console.debug'], // 移除指定函数
          // 高级压缩选项
          passes: 2,               // 压缩 passes 次数
          hoist_funs: true,        // 函数提升
          hoist_vars: true,        // 变量提升
          reduce_vars: true,       // 变量优化
          reduce_funcs: true,      // 函数优化
          unused: true,            // 移除未使用代码
          dead_code: true,         // 移除死代码
          collapse_vars: true,     // 变量合并
          collapse_static: true    // 静态属性合并
        },
        mangle: {
          safari10: true           // 兼容 Safari 10
        },
        format: {
          comments: false,         // 移除注释
          ascii_only: true         // 仅 ASCII 字符，避免中文乱码
        }
      },

      // Rollup 打包配置
      rollupOptions: {
        output: {
          // 代码分割策略
          manualChunks: {
            // 框架核心库
            'vue-vendor': ['vue', 'vue-router', 'pinia'],
            // UI 组件库
            'ui-vendor': ['element-plus', '@element-plus/icons-vue'],
            // HTTP 工具
            'http-vendor': ['axios']
          },
          // 资源文件命名规则
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name || ''
            if (info.endsWith('.css')) {
              return 'assets/css/[name]-[hash][extname]'
            }
            if (/\.(png|jpe?g|gif|svg|webp|ico)$/.test(info)) {
              return 'assets/images/[name]-[hash][extname]'
            }
            if (/\.(woff2?|eot|ttf|otf)$/.test(info)) {
              return 'assets/fonts/[name]-[hash][extname]'
            }
            return 'assets/[name]-[hash][extname]'
          }
        }
      },

      // 资源内联阈值（小于 4KB 内联为 base64）
      assetsInlineLimit: 4096,

      // 源码映射（生产环境关闭）
      sourcemap: false,

      // 目标浏览器
      target: 'es2015',

      // 报告压缩后大小
      reportCompressedSize: true
    },

    // 依赖预构建优化
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'pinia',
        'axios',
        'element-plus',
        '@element-plus/icons-vue'
      ],
      exclude: []
    },

    // CSS 配置
    css: {
      devSourcemap: true,
      preprocessorOptions: {
        scss: {
          additionalData: `@use "@/styles/vars.scss" as *;`
        }
      }
    },

    // 预览配置
    preview: {
      port: 4173,
      host: true
    }
  }
})
