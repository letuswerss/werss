import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// 主题类型
export type Theme = 'dark' | 'light' | 'system'

// Sidebar 状态类型
export type SidebarState = 'expanded' | 'collapsed'

// 应用状态接口
interface AppState {
  // 主题相关
  theme: Theme
  setTheme: (theme: Theme) => void

  // Sidebar 相关
  sidebarOpen: boolean
  sidebarState: SidebarState
  setSidebarOpen: (open: boolean) => void
  setSidebarState: (state: SidebarState) => void
  toggleSidebar: () => void

  // 移动端 Sidebar
  sidebarOpenMobile: boolean
  setSidebarOpenMobile: (open: boolean) => void
  toggleSidebarMobile: () => void
}

/** 首屏同步读取持久化主题（避免 persist 异步恢复前 store 仍为 system，导致误跟系统浅色） */
export function readPersistedTheme(): Theme {
  if (typeof window === 'undefined') return 'system'
  try {
    const raw = localStorage.getItem('app-storage')
    if (raw) {
      const t = JSON.parse(raw)?.state?.theme
      if (t === 'dark' || t === 'light' || t === 'system') return t
    }
    const legacy = localStorage.getItem('vite-ui-theme')
    if (legacy === 'dark' || legacy === 'light' || legacy === 'system') return legacy
  } catch {
    /* ignore */
  }
  return 'system'
}

// 应用主题到 DOM（与 Tailwind darkMode: class 一致，需给 html 加 light/dark 类）
export const applyTheme = (theme: Theme) => {
  if (typeof window === 'undefined') return

  const root = window.document.documentElement
  const body = window.document.body

  root.classList.remove('light', 'dark')
  root.removeAttribute('data-theme')
  body.classList.remove('dark-mode')

  if (theme === 'system') {
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light'

    root.classList.add(systemTheme)
    if (systemTheme === 'dark') {
      root.setAttribute('data-theme', 'dark')
      body.classList.add('dark-mode')
    }
  } else {
    root.classList.add(theme)
    if (theme === 'dark') {
      root.setAttribute('data-theme', 'dark')
      body.classList.add('dark-mode')
    }
  }
}

// 创建 store
export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // 主题状态（与 localStorage 同步初始化，避免首帧 theme=system 触发错误逻辑）
      theme: readPersistedTheme(),
      setTheme: (theme: Theme) => {
        set({ theme })
        applyTheme(theme)
        try {
          localStorage.setItem('vite-ui-theme', theme)
        } catch {
          /* ignore */
        }
      },

      // Sidebar 状态
      sidebarOpen: true,
      sidebarState: 'expanded',
      setSidebarOpen: (open: boolean) => {
        set({
          sidebarOpen: open,
          sidebarState: open ? 'expanded' : 'collapsed'
        })
      },
      setSidebarState: (state: SidebarState) => {
        set({
          sidebarState: state,
          sidebarOpen: state === 'expanded'
        })
      },
      toggleSidebar: () => {
        const { sidebarOpen } = get()
        set({
          sidebarOpen: !sidebarOpen,
          sidebarState: !sidebarOpen ? 'expanded' : 'collapsed'
        })
      },

      // 移动端 Sidebar
      sidebarOpenMobile: false,
      setSidebarOpenMobile: (open: boolean) => {
        set({ sidebarOpenMobile: open })
      },
      toggleSidebarMobile: () => {
        const { sidebarOpenMobile } = get()
        set({ sidebarOpenMobile: !sidebarOpenMobile })
      },
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({
        theme: state.theme,
        sidebarOpen: state.sidebarOpen,
        sidebarState: state.sidebarState,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.theme) {
          applyTheme(state.theme)
          try {
            localStorage.setItem('vite-ui-theme', state.theme)
          } catch {
            /* ignore */
          }
        }
      },
    }
  )
)

// 主题相关的便捷 hooks
export const useTheme = () => {
  const theme = useAppStore((state) => state.theme)
  const setTheme = useAppStore((state) => state.setTheme)
  return { theme, setTheme }
}

// Sidebar 相关的便捷 hooks
export const useSidebarStore = () => {
  const sidebarOpen = useAppStore((state) => state.sidebarOpen)
  const sidebarState = useAppStore((state) => state.sidebarState)
  const setSidebarOpen = useAppStore((state) => state.setSidebarOpen)
  const setSidebarState = useAppStore((state) => state.setSidebarState)
  const toggleSidebar = useAppStore((state) => state.toggleSidebar)
  const sidebarOpenMobile = useAppStore((state) => state.sidebarOpenMobile)
  const setSidebarOpenMobile = useAppStore((state) => state.setSidebarOpenMobile)
  const toggleSidebarMobile = useAppStore((state) => state.toggleSidebarMobile)

  return {
    sidebarOpen,
    sidebarState,
    setSidebarOpen,
    setSidebarState,
    toggleSidebar,
    sidebarOpenMobile,
    setSidebarOpenMobile,
    toggleSidebarMobile,
  }
}
