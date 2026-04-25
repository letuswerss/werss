# 状态管理 (State Management)

项目使用 [Zustand](https://github.com/pmndrs/zustand) 进行全局状态管理。

## 功能

### 1. 主题管理 (Theme)

统一管理应用的主题状态（浅色/深色/跟随系统）。

```tsx
import { useTheme } from '@/store'

function MyComponent() {
  const { theme, setTheme } = useTheme()
  
  return (
    <button onClick={() => setTheme('dark')}>
      当前主题: {theme}
    </button>
  )
}
```

### 2. Sidebar 状态管理

统一管理侧边栏的展开/收起状态。

```tsx
import { useSidebarStore } from '@/store'

function MyComponent() {
  const { 
    sidebarOpen, 
    sidebarState, 
    toggleSidebar,
    setSidebarOpen 
  } = useSidebarStore()
  
  return (
    <button onClick={toggleSidebar}>
      Sidebar: {sidebarState}
    </button>
  )
}
```

## Store 结构

所有状态都存储在 `useAppStore` 中，并自动持久化到 localStorage。

### 持久化

以下状态会自动保存到 localStorage：
- `theme`: 主题设置
- `sidebarOpen`: Sidebar 展开状态
- `sidebarState`: Sidebar 状态（expanded/collapsed）

### 访问 Store

```tsx
import { useAppStore } from '@/store'

// 直接访问整个 store
const store = useAppStore()

// 或者选择性订阅（推荐，性能更好）
const theme = useAppStore((state) => state.theme)
const setTheme = useAppStore((state) => state.setTheme)
```

## 向后兼容

为了保持向后兼容，以下组件仍然可以正常工作：
- `useTheme()` hook（从 `@/components/theme-provider` 或 `@/store` 导入都可以）
- `useSidebar()` hook（从 `@/components/ui/sidebar` 导入）

## 优势

1. **统一管理**: 所有全局状态集中在一个地方
2. **自动持久化**: 状态自动保存到 localStorage
3. **类型安全**: 完整的 TypeScript 支持
4. **性能优化**: 只订阅需要的状态，避免不必要的重渲染
5. **轻量级**: Zustand 体积小，API 简单
