import React from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useLocation } from 'react-router-dom'
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarRail,
  SidebarGroup,
  SidebarGroupLabel,
} from '@/components/ui/sidebar'
import {
  FileText,
  Rss,
  Tag,
  Settings,
  Info,
  LayoutDashboard,
  Key,
  Layers3,
  ChevronRight,
  Zap,
  Flame,
  Clock,
  Download,
  Send
} from 'lucide-react'
import { cn } from '@/lib/utils'

const Navbar: React.FC = () => {
  const { t } = useTranslation()
  const location = useLocation()
  
  // 使用 Vite BASE_URL 自动适配 dev(`/`) 与生产(`/static/`) 环境
  const logo = `${import.meta.env.BASE_URL}logo.svg`
  const appTitle = import.meta.env.VITE_APP_TITLE || 'WeRSS 微信公众文章热度分析系统'

  // 顺序：数据概览 → 订阅 → 文章 → 标签 → 抓取 → 标签聚类 → 热点 → 推送；导出与系统类置后
  const menuItems = [
    {
      title: t('layout.dashboard'),
      url: '/dashboard',
      icon: LayoutDashboard,
    },
    {
      title: t('layout.subscriptions'),
      url: '/subscriptions',
      icon: Rss,
    },
    {
      title: t('layout.articles'),
      url: '/articles',
      icon: FileText,
    },
    {
      title: t('layout.tags'),
      url: '/tags',
      icon: Tag,
    },
    {
      title: t('layout.fetchTasks'),
      url: '/fetch-tasks',
      icon: Download,
    },
    {
      title: t('layout.tagClusters'),
      url: '/tag-clusters',
      icon: Layers3,
    },
    {
      title: t('layout.hotTopicsDiscovery'),
      url: '/hot-topics',
      icon: Flame,
    },
    {
      title: t('layout.notifyTasks'),
      url: '/notify-tasks',
      icon: Send,
    },
    {
      title: t('layout.exportRecords'),
      url: '/export/records',
      icon: FileText,
    },
    {
      title: t('layout.systemTasks'),
      url: '/system-tasks',
      icon: Clock,
    },
    {
      title: t('layout.configs'),
      url: '/configs',
      icon: Settings,
    },
    {
      title: t('layout.sysInfo'),
      url: '/sys-info',
      icon: Info,
    },
    {
      title: t('layout.apiKeys'),
      url: '/api-keys',
      icon: Key,
    }
  ]

  return (
    <Sidebar collapsible="icon" className="border-r border-sidebar-border bg-sidebar shadow-sm">
      <SidebarHeader className="h-16 flex items-center px-4 border-b border-sidebar-border bg-sidebar">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild className="hover:bg-transparent active:bg-transparent">
              <Link to="/" className="flex items-center gap-3">
                <div className="flex-shrink-0 bg-primary h-8 w-8 rounded-lg flex items-center justify-center shadow-lg shadow-primary/20 transition-transform group-hover:scale-105">
                  {logo ? (
                    <img 
                      src={logo} 
                      alt={appTitle} 
                      className="h-5 w-5 object-contain" 
                    />
                  ) : (
                    <Zap className="h-5 w-5 text-white" />
                  )}
                </div>
                <div className="flex flex-col gap-0.5 leading-none min-w-0">
                  <span className="font-bold text-sidebar-foreground tracking-tight whitespace-nowrap overflow-hidden group-data-[collapsible=icon]:hidden">
                    {appTitle.split(' ')[0]}
                  </span>
                  <span className="text-[10px] font-medium text-primary/70 uppercase tracking-widest group-data-[collapsible=icon]:hidden">
                    Heat Analysis v1.1
                  </span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      
      <SidebarContent className="px-2 py-4 bg-sidebar">
        <SidebarGroup>
          <SidebarGroupLabel className="px-2 text-[11px] font-bold text-sidebar-foreground/50 uppercase tracking-[0.15em] mb-2">
            主控中心
          </SidebarGroupLabel>
          <SidebarMenu className="gap-1">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.url || (item.url !== '/' && location.pathname.startsWith(item.url))
              
              return (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton 
                    asChild 
                    tooltip={item.title} 
                    className={cn(
                      "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all duration-200",
                      isActive 
                        ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm font-semibold" 
                        : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                    )}
                  >
                    <Link to={item.url}>
                      <Icon className={cn(
                        "h-5 w-5 transition-colors",
                        isActive ? "text-primary" : "text-sidebar-foreground/40 group-hover:text-sidebar-foreground/70"
                      )} />
                      <span className="flex-grow group-data-[collapsible=icon]:hidden">{item.title}</span>
                      {isActive && (
                        <>
                          <ChevronRight className="h-3.5 w-3.5 opacity-50 ml-auto group-data-[collapsible=icon]:hidden" />
                          <div className="absolute left-0 w-1 h-6 bg-primary rounded-r-full" />
                        </>
                      )}
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              )
            })}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      
      <SidebarRail />
    </Sidebar>
  )
}

export default Navbar
