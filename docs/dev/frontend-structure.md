# 前端结构

本文档面向要修改 `web_ui/` 的开发者。目标不是列目录，而是解释当前前端是怎么和后端、权限、页面状态配合工作的。

## 1. 前端的角色

当前前端是一个 React 18 + TypeScript + Vite 的管理台，不是“纯展示站”。它承担 4 类职责：

- 页面路由和登录拦截
- 调后端 API 并把返回结构转成页面状态
- 提供批量操作、弹窗、表格、筛选等后台交互
- 管理少量本地状态，比如主题、任务恢复状态

前端不应该自己重新实现后端业务规则。比如：

- AI 过滤结果怎么判断
- 热点怎么聚类
- 标签怎么抽取

这些都应来自后端。

## 2. 入口与路由

### `src/main.tsx`

这里只负责挂载应用。

### `src/router/index.tsx`

这是前端的真正入口。建议先读这个文件，因为它直接告诉你系统有哪些页面。

当前关键路由包括：

- `/`
- `/articles`
- `/subscriptions`
- `/dashboard`
- `/settings`
- `/add-subscription`
- `/wechat/mp`
- `/configs`
- `/export/records`
- `/message-tasks`
- `/sys-info`
- `/tags`
- `/tag-clusters`
- `/hot-topics`
- `/api-keys`

这里还有两层包装：

- `ProtectedRoute`
  没 token 就跳登录页。
- `PermissionRoute`
  预留权限检查入口。

如果你新增页面但访问不到，第一件事不是查组件，而是看是否已经加入 [web_ui/src/router/index.tsx](../../web_ui/src/router/index.tsx)。

## 3. 目录怎么读

`web_ui/src/` 可以按下面方式理解：

- `views/`
  页面级组件。通常一个文件对应一个页面。
- `api/`
  按领域封装后端接口。
- `components/`
  可复用组件和布局。
- `router/`
  路由定义。
- `hooks/`
  自定义 hooks。
- `store/`
  全局状态，例如主题。
- `utils/`
  日期、消息提示、常量等工具。
- `types/`
  接口类型定义。

页面逻辑应该尽量留在 `views/`，接口封装放到 `api/`，不要把 `fetch` 或 `axios` 直接散落在组件里。

## 4. 页面层：`views/`

当前可以分成 4 类页面：

### 4.1 内容主链路

- `ArticleListPage.tsx`
  文章工作台。
- `SubscriptionManagement.tsx`
  订阅管理。
- `AddSubscription.tsx`
  添加订阅。

### 4.2 分析与整理

- `TagList.tsx`
  标签管理。
- `TagClusterList.tsx`
  标签聚类列表。
- `TagClusterDetail.tsx`
  聚类详情。
- `HotTopics.tsx`
  热点发现。

### 4.3 系统运营

- `MessageTaskList.tsx`
- `MessageTaskForm.tsx`
- `Settings.tsx`
- `ConfigList.tsx`
- `ConfigDetail.tsx`
- `SysInfo.tsx`
- `ApiKeyManagement.tsx`

### 4.4 认证与用户

- `Login.tsx`
- `ChangePassword.tsx`
- `EditUser.tsx`

改页面前，先判断你是在改“列表页”、“表单页”还是“详情页”，不同页面的状态组织方式差别很大。

## 5. 组件层：`components/`

前端里最重要的不是原子组件，而是这些承载系统骨架的组件：

- `components/Layout/BasicLayout`
  登录后整个后台框架。
- `components/ui/*`
  基础 UI 组件。
- `components/SystemResources`
  系统资源卡片。
- 文章导出、消息提示、分页等业务组件

如果你改导航、右上角用户信息、菜单结构，一般落在 `BasicLayout`。

## 6. API 层：`api/`

`api/` 目录按后端领域分文件：

- `article.ts`
- `subscription.ts`
- `tags.ts`
- `tagCluster.ts`
- `hotTopics.ts`
- `messageTask.ts`
- `configManagement.ts`
- `apiKey.ts`
- `sysInfo.ts`

这里的规则应该是：

- 一个后端领域对应一个前端 API 文件
- 统一处理请求参数和返回值
- 页面不要重复拼 URL

如果一个页面同时发很多接口请求，优先检查能不能先补 API 封装，而不是在组件里临时写。

## 7. 状态管理怎么分层

当前前端有 3 类状态：

### 7.1 页面内局部状态

例如：

- 当前页码
- 搜索词
- 当前选中的文章
- 弹窗开关

这些大多用 `useState` 放在页面组件里。

### 7.2 可跨组件复用的全局状态

例如：

- 主题
- 可能的用户信息

这类状态放在 `store/`。

### 7.3 本地持久化状态

例如文章 AI 过滤任务会把一部分状态存到 `localStorage`，用于中断恢复。

不要把“临时页面状态”随意放全局。只有跨页面、跨组件或需要恢复的状态才值得提升。

## 8. 几个关键页面的实现特点

### 文章列表页

[web_ui/src/views/ArticleListPage.tsx](../../web_ui/src/views/ArticleListPage.tsx) 是最复杂的页面之一，主要特征：

- 顶部筛选
- 公众号下拉
- 批量操作
- AI 过滤任务恢复
- 标签提取任务
- 导出
- 文章详情抽屉 / 弹窗

这里适合做增量改造，不适合一次性大重构。

### 订阅管理页

[web_ui/src/views/SubscriptionManagement.tsx](../../web_ui/src/views/SubscriptionManagement.tsx) 是“列表 + 详情”双栏页：

- 左侧列表
- 右侧详情
- 支持直接刷新采集
- 支持编辑 / 删除

如果你要加新字段，一般要同时改列表区和详情区。

### 设置页

[web_ui/src/views/Settings.tsx](../../web_ui/src/views/Settings.tsx) 不是简单偏好页，它混合了：

- 本地 UI 设置
- 配置管理 API
- 系统调度器信息
- 文章清理策略
- Prompt 模板

所以改设置页前，要先分清楚：

- 这是纯前端设置
- 还是会写入后端配置
- 还是只读系统状态

## 9. 新增一个页面的正确方式

建议按这个顺序：

1. 在 `views/` 新建页面组件
2. 在 `api/` 补接口封装
3. 在 `router/index.tsx` 注册路由
4. 需要时把菜单入口加到布局组件
5. 补类型定义和空态 / 错态

不要先把页面写完再回头补 API；那样通常会把返回结构假设错。

## 10. 最容易踩的坑

- 改了页面但没同步 `router`。
- 直接在页面里手写请求逻辑，后面无法复用。
- 把权限问题当成前端问题，其实是后端没拦。
- 没看后端实际返回结构，就按旧接口印象写页面。
- 列表页只改展示，不改分页和筛选逻辑。

## 11. 建议阅读顺序

第一次进前端建议按这个顺序读：

1. [web_ui/src/router/index.tsx](../../web_ui/src/router/index.tsx)
2. [web_ui/src/components/Layout/BasicLayout.tsx](../../web_ui/src/components/Layout/BasicLayout.tsx)
3. [web_ui/src/views/ArticleListPage.tsx](../../web_ui/src/views/ArticleListPage.tsx)
4. [web_ui/src/views/SubscriptionManagement.tsx](../../web_ui/src/views/SubscriptionManagement.tsx)
5. [web_ui/src/views/Settings.tsx](../../web_ui/src/views/Settings.tsx)

这样最容易抓住项目的前端主干。
