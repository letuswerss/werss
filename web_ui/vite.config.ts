import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig(({ command, mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), "");

  return {
    appType: 'spa', // 明确指定为 SPA 应用，确保所有路由都回退到 index.html
    plugins: [
      react({
        jsxRuntime: 'automatic',
      }),
    ],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    base: command === 'build' ? '/static/' : '/',
    
    build: {
      outDir: "dist",
      emptyOutDir: true,
      assetsDir: "assets",
      chunkSizeWarningLimit: 2000, // 调大警告阈值，因为我们合并了包
      
      // ⚠️ 关键修改 1: 降低构建目标版本
      // 'esnext' 有时会导致 class 这里的初始化顺序问题，es2020 更稳健
      target: 'es2020', 

      rollupOptions: {
        // 处理循环依赖警告
        onwarn(warning, warn) {
          // 忽略循环依赖警告（这些通常不会影响功能）
          if (warning.code === 'CIRCULAR_DEPENDENCY') {
            return;
          }
          // 忽略动态导入警告（这些是预期的）
          if (warning.message && warning.message.includes('dynamically imported')) {
            return;
          }
          warn(warning);
        },
        output: {
          // ⚠️ 关键修改 2: 优化分包策略，解决循环依赖
          manualChunks: (id) => {
            if (id.includes('node_modules')) {
              // 1. 只把 Monaco Editor 拆出来 (它非常独立，拆分很安全)
              if (id.includes('monaco-editor') || id.includes('@monaco-editor')) {
                return 'monaco';
              }

              // 2. ⚠️ 重点：不再单独拆分 vchart
              // 将 vchart, react, radix 等全部归入 vendor。
              // 这会增加 vendor.js 的体积，但能确保所有依赖在同一个闭包内按正确顺序执行。
              return 'vendor';
            }
            // 3. 将 API 模块单独拆分，避免循环依赖
            // 这样可以确保动态导入和静态导入都能正常工作
            if (id.includes('/src/api/')) {
              return 'api';
            }
          },
          inlineDynamicImports: false,
          chunkFileNames: 'assets/[name]-[hash].js',
          entryFileNames: 'assets/[name]-[hash].js',
          assetFileNames: 'assets/[name]-[hash].[ext]',
        },
      },
      commonjsOptions: {
        transformMixedEsModules: true,
      },
    },
    
    server: {
      host: "0.0.0.0",
      port: 5173,
      // 确保 SPA 路由正确回退到 index.html
      fs: {
        strict: false,
      },
      proxy: {
        "/static/res": createProxyTarget(env),
        "/files": createProxyTarget(env),
        "/rss": createProxyTarget(env),
        "/feed": createProxyTarget(env),
        "/api": createProxyTarget(env),
        "/test-results": {
          target: "http://localhost:8001",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/test-results/, '/test-results'),
        },
      },
    },
    // 确保预览模式也正确处理 SPA 路由
    preview: {
      port: 5173,
    },
  };
});

/**
 * 辅助函数：生成代理配置
 */
function createProxyTarget(env: Record<string, string>) {
  const target = env.VITE_API_BASE_URL || "http://127.0.0.1:8001";
  return {
    target,
    changeOrigin: true,
    secure: false,
    ws: true,
    configure: (proxy: any, _options: any) => {
      proxy.on('error', (err: any, req: any, res: any) => {
        if (err?.code !== 'ECONNREFUSED') {
          console.log(`[vite] proxy error: ${err?.message || err}`);
        }
        if (err?.code === 'ECONNREFUSED' && res && !res.headersSent) {
          res.writeHead(404, { 'Content-Type': 'text/plain' });
          res.end('Backend server not available (Proxy Error)');
        }
      });
    },
  };
}