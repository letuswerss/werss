# 微信公众号热度分析系统 - WebUI

基于 React + TypeScript + Vite 构建的现代化前端界面

## 功能列表

### 核心功能
- 用户认证（登录/登出）
- 文章列表展示（支持桌面端和移动端响应式布局）
- 订阅管理（添加、编辑、删除公众号订阅）
- 仪表板（数据统计和可视化）
- 小说阅读器

### 管理功能
- 配置管理（系统配置的查看和编辑）
- 消息任务管理（定时消息任务的创建和管理）
- 标签管理（文章标签的创建和管理）
- 微信公众账号管理
- 导出记录查看

### 用户功能
- 用户信息编辑
- 密码修改
- 系统设置（包括暗色模式切换）
- 系统信息查看

## 安装依赖

推荐使用 `pnpm` 进行包管理：

```bash
pnpm install
```

或使用 `npm`：

```bash
npm install
```

## 环境变量配置

创建 `.env` 文件：

```ini
VITE_API_BASE_URL=http://your-api-server.com
```

## 运行项目

开发模式：
```bash
pnpm dev
# 或
npm run dev
```

生产构建：
```bash
pnpm build
# 或
npm run build
```

预览生产构建：
```bash
pnpm preview
# 或
npm run preview
```

## 测试

运行 Playwright 测试：
```bash
pnpm test
# 或
npm run test
```

带 UI 的测试：
```bash
pnpm test:ui
# 或
npm run test:ui
```

## 项目结构

```
src/
├── api/                # API 接口封装
├── assets/             # 静态资源
├── components/         # 公共组件
│   ├── Layout/        # 布局组件
│   ├── ui/            # UI 基础组件（基于 Radix UI）
│   └── extensions/    # 扩展组件
├── hooks/              # React Hooks
├── lib/                # 工具库
├── router/             # 路由配置
├── types/              # TypeScript 类型定义
├── utils/              # 工具函数
├── views/              # 页面组件
├── App.tsx             # 根组件
└── main.tsx            # 入口文件
```

## 技术栈

### 核心框架
- **React 18** - UI 框架
- **TypeScript** - 类型系统
- **Vite** - 构建工具

### UI 组件库
- **Radix UI** - 无样式、可访问的 UI 组件
- **Tailwind CSS** - 实用优先的 CSS 框架
- **shadcn/ui** - 基于 Radix UI 的组件系统

### 路由和状态
- **React Router v6** - 路由管理
- **React Hook Form** - 表单管理
- **Zod** - 数据验证

### 其他工具
- **Axios** - HTTP 客户端
- **date-fns** - 日期处理
- **Monaco Editor** - 代码编辑器
- **VChart** - 数据可视化
- **Playwright** - 端到端测试

## 特性

- 🎨 支持暗色模式
- 📱 响应式设计，支持移动端和桌面端
- ♿ 良好的可访问性支持
- 🚀 快速的开发体验（Vite HMR）
- 🔒 路由守卫和权限控制
- 📊 数据可视化图表
- 🌐 国际化支持（i18n）