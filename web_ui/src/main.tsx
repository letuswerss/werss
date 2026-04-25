import React from 'react'
import ReactDOM from 'react-dom/client'
import router from './router'
import { RouterProvider } from 'react-router-dom'
import { initSettings } from './utils/settings'
import { Toaster } from '@/components/ui/sonner'
import { ThemeProvider } from '@/components/theme-provider'

// 导入 i18n 配置（必须在其他导入之前初始化）
import './i18n/config'

// 导入自定义样式
import './style.css'

// 初始化设置（包括暗色模式）
initSettings()

ReactDOM.createRoot(document.getElementById('app')!).render(
  <React.StrictMode>
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <RouterProvider 
        router={router}
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
        fallbackElement={
          <div className="flex items-center justify-center h-screen">
            <div className="text-center">
              <div className="text-lg font-semibold mb-2">加载中...</div>
            </div>
          </div>
        }
      />
      <Toaster />
    </ThemeProvider>
  </React.StrictMode>
)
