# Tailwind CSS 迁移指南

项目已配置 Tailwind CSS，可以逐步将单独的 CSS 文件迁移到 Tailwind 工具类。

## 安装依赖

```bash
npm install
# 或
pnpm install
```

## 使用方式

### 1. 在组件中使用 Tailwind 类

```tsx
// 之前 (使用 CSS 文件)
<div className="login-container">
  <div className="login-layout">
    ...
  </div>
</div>

// 之后 (使用 Tailwind)
<div className="h-screen p-0 m-0 bg-gradient-to-br from-blue-500/95 to-purple-500/90 bg-[length:200%_200%] animate-[gradientBG_12s_ease_infinite]">
  <div className="flex h-full transition-all duration-300">
    ...
  </div>
</div>
```

### 2. 常用 Tailwind 类对照

| CSS | Tailwind |
|-----|----------|
| `display: flex` | `flex` |
| `justify-content: center` | `justify-center` |
| `align-items: center` | `items-center` |
| `padding: 1rem` | `p-4` |
| `margin: 1rem` | `m-4` |
| `width: 100%` | `w-full` |
| `height: 100vh` | `h-screen` |
| `border-radius: 8px` | `rounded-lg` |
| `background-color: #fff` | `bg-white` |
| `color: #333` | `text-gray-800` |
| `font-weight: 500` | `font-medium` |
| `transition: all 0.3s` | `transition-all duration-300` |

### 3. 自定义颜色

已在 `tailwind.config.js` 中配置了项目主题色：

- `text-primary` - 主色文字
- `bg-primary` - 主色背景
- `text-success` - 成功色
- `text-warning` - 警告色
- `text-danger` - 危险色

### 4. 响应式设计

```tsx
// 移动端优先
<div className="w-full md:w-1/2 lg:w-1/3">
  {/* 默认全宽，中等屏幕一半，大屏幕三分之一 */}
</div>
```

### 5. 保留必要的 CSS 文件

以下情况建议保留 CSS 文件：
- 复杂的动画（如 `@keyframes`）
- 第三方组件样式覆盖
- 特殊的伪元素样式

### 6. 迁移步骤

1. 选择一个组件
2. 查看其 CSS 文件
3. 将样式转换为 Tailwind 类
4. 删除 CSS 文件引用
5. 测试组件外观和功能

## 示例：Login 组件迁移

查看 `src/views/Login.tsx` 和 `src/views/Login.css` 的迁移示例。

