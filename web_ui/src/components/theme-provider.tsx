import { useEffect } from "react"
import { useAppStore } from "@/store"

type ThemeProviderProps = {
  children: React.ReactNode
  defaultTheme?: "dark" | "light" | "system"
  storageKey?: string
}

// 为了向后兼容，保留 ThemeProvider 组件
export function ThemeProvider({
  children,
  defaultTheme: _defaultTheme = "system",
  storageKey: _storageKey = "vite-ui-theme",
}: ThemeProviderProps) {
  const { theme } = useAppStore()

  // 主题持久化由 zustand persist（app-storage）与 initSettings 首屏 apply 负责；
  // 不再在挂载时读取 vite-ui-theme 并 setTheme，否则会覆盖 app-storage（旧键常为 light）。

  // 监听系统主题变化
  useEffect(() => {
    if (theme !== "system") return

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
    const handleChange = () => {
      const root = window.document.documentElement
      const body = window.document.body
      const systemTheme = mediaQuery.matches ? "dark" : "light"

      root.classList.remove("light", "dark")
      root.removeAttribute("data-theme")
      body.classList.remove("dark-mode")

      root.classList.add(systemTheme)
      if (systemTheme === "dark") {
        root.setAttribute("data-theme", "dark")
        body.classList.add("dark-mode")
      }
    }

    handleChange()
    mediaQuery.addEventListener("change", handleChange)
    return () => mediaQuery.removeEventListener("change", handleChange)
  }, [theme])

  return <>{children}</>
}

// 导出 useTheme hook（从 store 中导出，保持 API 兼容）
export { useTheme } from "@/store"
