import { createBrowserRouter, Navigate, Link } from 'react-router-dom'
import NotFound from '../views/NotFound'
import BasicLayout from '../components/Layout/BasicLayout'
import ExportRecords from '../views/ExportRecords'
import Login from '../views/Login'
import ArticleListPage from '../views/ArticleListPage'
import ChangePassword from '../views/ChangePassword'
import EditUser from '../views/EditUser'
import AddSubscription from '../views/AddSubscription'
import WeChatMpManagement from '../views/WeChatMpManagement'
import SubscriptionManagement from '../views/SubscriptionManagement'
import ConfigList from '../views/ConfigList'
import ConfigDetail from '../views/ConfigDetail'
import MessageTaskList from '../views/MessageTaskList'
import MessageTaskForm from '../views/MessageTaskForm'
import FetchTaskList from '../views/FetchTaskList'
import FetchTaskForm from '../views/FetchTaskForm'
import NotifyTaskList from '../views/NotifyTaskList'
import NotifyTaskForm from '../views/NotifyTaskForm'
import SystemTaskList from '../views/SystemTaskList'
import NovelReader from '../views/NovelReader'
import SysInfo from '../views/SysInfo'
import TagList from '../views/TagList'
import TagForm from '../views/TagForm'
import TagClusterList from '../views/TagClusterList'
import TagClusterDetail from '../views/TagClusterDetail'
import HotTopics from '../views/HotTopics'
import Dashboard from '../views/Dashboard'
import Settings from '../views/Settings'
import ApiKeyManagement from '../views/ApiKeyManagement'
// import { verifyToken } from '@/api/auth'

// 路由守卫组件
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token')
  
  if (!token) {
    const currentPath = window.location.pathname + window.location.search
    return <Navigate to={`/login?redirect=${encodeURIComponent(currentPath)}`} replace />
  }
  
  return <>{children}</>
}

// 权限检查组件
const PermissionRoute = ({ 
  children, 
  permissions 
}: { 
  children: React.ReactNode
  permissions?: string[] 
}) => {
  // 这里可以添加权限检查逻辑
  return <>{children}</>
}

const router = createBrowserRouter(
  [
  {
    path: '/login',
    element: <Login />
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <BasicLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <ArticleListPage />
      },
      {
        path: 'articles',
        element: <ArticleListPage />
      },
      {
        path: 'subscriptions',
        element: <SubscriptionManagement />
      },
      {
        path: 'subscriptions/:id',
        element: <SubscriptionManagement />
      },
      {
        path: 'dashboard',
        element: <Dashboard />
      },
      {
        path: 'change-password',
        element: <ChangePassword />
      },
      {
        path: 'edit-user',
        element: <EditUser />
      },
      {
        path: 'settings',
        element: <Settings />
      },
      {
        path: 'add-subscription',
        element: <AddSubscription />
      },
      {
        path: 'wechat/mp',
        element: (
          <PermissionRoute permissions={['wechat:manage']}>
            <WeChatMpManagement />
          </PermissionRoute>
        )
      },
      {
        path: 'configs',
        element: (
          <PermissionRoute permissions={['config:view']}>
            <ConfigList />
          </PermissionRoute>
        )
      },
      {
        path: 'export/records',
        element: (
          <PermissionRoute permissions={['config:view']}>
            <ExportRecords />
          </PermissionRoute>
        )
      },
      {
        path: 'configs/:key',
        element: (
          <PermissionRoute permissions={['config:view']}>
            <ConfigDetail />
          </PermissionRoute>
        )
      },
      {
        path: 'message-tasks',
        element: (
          <PermissionRoute permissions={['message_task:view']}>
            <MessageTaskList />
          </PermissionRoute>
        )
      },
      {
        path: 'message-tasks/add',
        element: (
          <PermissionRoute permissions={['message_task:edit']}>
            <MessageTaskForm />
          </PermissionRoute>
        )
      },
      {
        path: 'message-tasks/edit/:id',
        element: (
          <PermissionRoute permissions={['message_task:edit']}>
            <MessageTaskForm />
          </PermissionRoute>
        )
      },
      {
        path: 'system-tasks',
        element: (
          <PermissionRoute permissions={['message_task:view']}>
            <SystemTaskList />
          </PermissionRoute>
        )
      },
      {
        path: 'fetch-tasks',
        element: (
          <PermissionRoute permissions={['message_task:view']}>
            <FetchTaskList />
          </PermissionRoute>
        )
      },
      {
        path: 'fetch-tasks/add',
        element: (
          <PermissionRoute permissions={['message_task:edit']}>
            <FetchTaskForm />
          </PermissionRoute>
        )
      },
      {
        path: 'fetch-tasks/edit/:id',
        element: (
          <PermissionRoute permissions={['message_task:edit']}>
            <FetchTaskForm />
          </PermissionRoute>
        )
      },
      {
        path: 'notify-tasks',
        element: (
          <PermissionRoute permissions={['message_task:view']}>
            <NotifyTaskList />
          </PermissionRoute>
        )
      },
      {
        path: 'notify-tasks/add',
        element: (
          <PermissionRoute permissions={['message_task:edit']}>
            <NotifyTaskForm />
          </PermissionRoute>
        )
      },
      {
        path: 'notify-tasks/edit/:id',
        element: (
          <PermissionRoute permissions={['message_task:edit']}>
            <NotifyTaskForm />
          </PermissionRoute>
        )
      },
      {
        path: 'sys-info',
        element: (
          <PermissionRoute permissions={['admin']}>
            <SysInfo />
          </PermissionRoute>
        )
      },
      {
        path: 'tags',
        element: (
          <PermissionRoute permissions={['tag:view']}>
            <TagList />
          </PermissionRoute>
        )
      },
      {
        path: 'tags/add',
        element: (
          <PermissionRoute permissions={['tag:edit']}>
            <TagForm />
          </PermissionRoute>
        )
      },
      {
        path: 'tags/edit/:id',
        element: (
          <PermissionRoute permissions={['tag:edit']}>
            <TagForm />
          </PermissionRoute>
        )
      },
      {
        path: 'tag-clusters',
        element: (
          <PermissionRoute permissions={['tag:view']}>
            <TagClusterList />
          </PermissionRoute>
        )
      },
      {
        path: 'tag-clusters/:id',
        element: (
          <PermissionRoute permissions={['tag:view']}>
            <TagClusterDetail />
          </PermissionRoute>
        )
      },
      {
        path: 'hot-topics',
        element: <HotTopics />
      },
      {
        path: 'api-keys',
        element: (
          <PermissionRoute permissions={['admin']}>
            <ApiKeyManagement />
          </PermissionRoute>
        ),
        errorElement: (
          <div className="flex items-center justify-center h-screen">
            <div className="text-center">
              <h1 className="text-4xl font-bold mb-4">错误</h1>
              <p className="text-muted-foreground mb-4">加载 API Key 管理页面时出错</p>
              <Link to="/" className="text-primary hover:underline">返回首页</Link>
            </div>
          </div>
        )
      },
      {
        path: '*',
        element: <NotFound />
      }
    ]
  },
  {
    path: '/reader',
    element: (
      <ProtectedRoute>
        <NovelReader />
      </ProtectedRoute>
    )
  }
  ],
  {
    future: {
      v7_startTransition: true,
      v7_relativeSplatPath: true,
    },
  }
)

export default router
