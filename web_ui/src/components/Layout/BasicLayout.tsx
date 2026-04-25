import React, { useState, useEffect, useMemo, createContext, useContext } from 'react'
import { Outlet, useLocation, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '@/components/ui/dropdown-menu'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import { useToast } from '@/hooks/use-toast'
import Navbar from './Navbar'
import WechatAuthQrcode, { WechatAuthQrcodeRef } from '../WechatAuthQrcode'
import { logout } from '@/api/auth'
import { getUserInfo } from '@/api/user'
import { getSysInfo } from '@/api/sysInfo'
import { initBrowserNotification } from '@/utils/browserNotification'
import { getSettings, type AppSettings } from '@/utils/settings'
import { ModeToggle } from '@/components/mode-toggle'
import { User, Lock, QrCode, Settings, Bell, LogOut as LogoutIcon, UserCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AppContextType {
  showAuthQrcode: () => void
}

const AppContext = createContext<AppContextType | null>(null)

export const useAppContext = () => {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useAppContext must be used within BasicLayout')
  }
  return context
}

const BasicLayout: React.FC = () => {
  const { t } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()
  
  const [userInfo, setUserInfo] = useState({ username: '', nickname: '', avatar: '' })
  const [haswxLogined, setHaswxLogined] = useState(true)
  const [hasLogined, setHasLogined] = useState(false)
  const [settings, setSettings] = useState<AppSettings>(getSettings())
  const qrcodeRef = React.useRef<WechatAuthQrcodeRef>(null)
  const { toast } = useToast()

  const isAuthenticated = useMemo(() => {
    const token = localStorage.getItem('token')
    setHasLogined(!!token)
    return !!token
  }, [location.pathname])

  const appTitle = useMemo(
    () => import.meta.env.VITE_APP_TITLE || '微信公众号热度分析系统',
    []
  )

  const fetchUserInfo = async () => {
    try {
      const res = await getUserInfo() as unknown as {
        username: string
        nickname?: string
        avatar: string
      }
      setUserInfo({
        username: res.username || '',
        nickname: res.nickname || res.username || '',
        avatar: res.avatar || '',
      })
    } catch (error) {
      console.error(t('layout.getUserInfoFailed'), error)
    }
  }

  const fetchSysInfo = async () => {
    try {
      const res = await getSysInfo()
      setHaswxLogined(res?.wx?.login || false)
    } catch (error) {
      console.error('获取系统信息失败', error)
    }
  }

  const showAuthQrcode = () => {
    qrcodeRef.current?.startAuth()
  }

  const handleLogout = async () => {
    try {
      await logout()
      localStorage.removeItem('token')
      navigate('/login')
    } catch (error) {
      toast({
        variant: "destructive",
        title: t('common.error'),
        description: t('layout.logoutFailed')
      })
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      fetchUserInfo()
    }
    initBrowserNotification()
    fetchSysInfo()
    
    const handleSettingsChange = (e: CustomEvent<AppSettings>) => {
      setSettings(e.detail)
    }
    window.addEventListener('settingsChanged', handleSettingsChange as EventListener)
    return () => {
      window.removeEventListener('settingsChanged', handleSettingsChange as EventListener)
    }
  }, [])

  useEffect(() => {
    setHasLogined(!!localStorage.getItem('token'))
    if (hasLogined) {
      fetchUserInfo()
    }
  }, [location.pathname])

  const routeNameMap: Record<string, string> = {
    '/': t('layout.home'),
    '/dashboard': t('layout.dashboard'),
    '/articles': t('layout.articles'),
    '/subscriptions': t('layout.subscriptions'),
    '/export/records': t('layout.exportRecords'),
    '/tags': t('layout.tags'),
    '/tag-clusters': t('layout.tagClusters'),
    '/hot-topics': t('layout.hotTopicsDiscovery'),
    '/message-tasks': t('layout.messageTasks'),
    '/configs': t('layout.configs'),
    '/sys-info': t('layout.sysInfo'),
    '/api-keys': t('layout.apiKeys'),
  }

  const getBreadcrumbItems = (): Array<{ label: string; path: string }> => {
    const pathSegments = location.pathname.split('/').filter(Boolean)
    const items: Array<{ label: string; path: string }> = []
    if (pathSegments.length === 0) return [{ label: t('layout.home'), path: '/' }]
    let currentPath = ''
    pathSegments.forEach((segment) => {
      currentPath += `/${segment}`
      let label = routeNameMap[currentPath] || segment
      if (currentPath.startsWith('/tag-clusters/') && pathSegments.length >= 2 && currentPath !== '/tag-clusters') {
        label = t('layout.tagClusterDetail')
      }
      items.push({ label, path: currentPath })
    })
    return items
  }

  const breadcrumbItems = getBreadcrumbItems()

  const layoutContent = location.pathname === '/login' ? (
    <div className="min-h-screen flex flex-col bg-background" id="main">
      <main className="flex-1 min-h-screen">
        <Outlet />
      </main>
    </div>
  ) : (
    <SidebarProvider>
      <Navbar />
      <SidebarInset className="bg-background min-w-0">
        <header className="sticky top-0 z-40 h-16 shrink-0 flex items-center gap-2 transition-all border-b border-border bg-background/80 backdrop-blur-md px-4 md:px-6 justify-between overflow-hidden">
          <div className="flex items-center gap-2 sm:gap-3 flex-1 min-w-0">
            <SidebarTrigger className="-ml-1 text-muted-foreground hover:text-primary transition-colors flex-shrink-0" />
            <Separator orientation="vertical" className="h-4 bg-border flex-shrink-0" />

            <div className="flex ml-1 sm:ml-4 overflow-hidden">
              <Breadcrumb>
                <BreadcrumbList className="flex-nowrap">
                  {breadcrumbItems.slice(-2).map((item, index, arr) => (
                    <React.Fragment key={item.path}>
                      {index > 0 && <BreadcrumbSeparator className="opacity-50" />}
                      <BreadcrumbItem className={index === 0 && arr.length > 1 ? "hidden sm:block" : ""}>
                        {index === arr.length - 1 ? (
                          <BreadcrumbPage className="font-semibold text-foreground truncate max-w-[80px] sm:max-w-[150px]">{item.label}</BreadcrumbPage>
                        ) : (
                          <BreadcrumbLink asChild>
                            <Link to={item.path} className="text-muted-foreground hover:text-primary transition-colors truncate max-w-[60px] sm:max-w-[120px]">{item.label}</Link>
                          </BreadcrumbLink>
                        )}
                      </BreadcrumbItem>
                    </React.Fragment>
                  ))}
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </div>

          {hasLogined && (
            <div className="flex items-center gap-1 sm:gap-4 flex-shrink-0 ml-2">
              <div className="flex items-center gap-0.5 sm:gap-2">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={showAuthQrcode}
                        className={cn(
                          "p-2 rounded-lg transition-all relative",
                          !haswxLogined 
                            ? "bg-destructive/10 text-destructive hover:bg-destructive/20" 
                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                        )}
                      >
                        <QrCode className="h-5 w-5" />
                        {!haswxLogined && <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-destructive rounded-full border-2 border-background"></span>}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>
                      {!haswxLogined ? t('layout.notAuthorized') : t('layout.clickToScan')}
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                <button className="hidden xs:flex p-2 text-muted-foreground hover:bg-muted hover:text-foreground rounded-lg transition-all relative">
                   <Bell className="h-5 w-5" />
                   <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary rounded-full border-2 border-background"></span>
                </button>
                
                <div className="scale-90 sm:scale-100">
                  <ModeToggle />
                </div>
              </div>

              <div className="h-8 w-px bg-border mx-1 hidden xs:block"></div>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="flex items-center cursor-pointer gap-2 p-1 rounded-full hover:bg-muted transition-all outline-none">
                    <div className="relative flex-shrink-0">
                      <Avatar className="h-8 w-8 sm:h-9 sm:w-9 border-2 border-background shadow-sm transition-transform active:scale-95">
                        {userInfo.avatar ? (
                          <AvatarImage src={userInfo.avatar} alt={userInfo.nickname || userInfo.username || 'avatar'} />
                        ) : (
                          <AvatarFallback className="bg-primary/5 text-primary">
                            <User className="h-5 w-5" />
                          </AvatarFallback>
                        )}
                      </Avatar>
                      <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-500 rounded-full border-2 border-background"></div>
                    </div>
                    <div className="hidden lg:block text-left mr-1">
                      <p className="text-sm font-bold text-foreground leading-tight truncate max-w-[80px]">{userInfo.nickname || userInfo.username}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5 font-medium uppercase tracking-tight">{t('layout.admin')}</p>
                    </div>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56 mt-2 border-border shadow-xl rounded-xl p-2">
                  <div className="px-2 py-2 mb-2">
                     <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest">{t('layout.personalCenter')}</p>
                  </div>
                  <DropdownMenuItem onClick={() => navigate('/edit-user')} className="rounded-lg py-2 cursor-pointer focus:bg-primary/10 focus:text-primary">
                    <UserCircle className="h-4 w-4 mr-2 opacity-70" />
                    {t('layout.personalCenter')}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/change-password')} className="rounded-lg py-2 cursor-pointer focus:bg-primary/10 focus:text-primary">
                    <Lock className="h-4 w-4 mr-2 opacity-70" />
                    {t('layout.changePassword')}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/settings')} className="rounded-lg py-2 cursor-pointer focus:bg-primary/10 focus:text-primary">
                    <Settings className="h-4 w-4 mr-2 opacity-70" />
                    {t('layout.settings')}
                  </DropdownMenuItem>
                  
                  <DropdownMenuSeparator className="my-2 bg-border" />
                  <DropdownMenuItem onClick={handleLogout} className="rounded-lg py-2 cursor-pointer text-destructive focus:bg-destructive/10 focus:text-destructive">
                    <LogoutIcon className="h-4 w-4 mr-2" />
                    {t('layout.logout')}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              <WechatAuthQrcode ref={qrcodeRef} />
            </div>
          )}
        </header>
        <main className="flex-1 p-3 sm:p-6 lg:p-8 min-w-0 overflow-x-hidden">
          <div className="max-w-[1600px] mx-auto w-full">
            <Outlet />
          </div>
        </main>
      </SidebarInset>
    </SidebarProvider>
  )

  const renderWatermark = () => {
    if (!settings.watermarkEnabled) return null
    const watermarkText = `${appTitle} · ${new Date().getFullYear()}`
    return (
      <div className="pointer-events-none fixed inset-0 z-[9999] overflow-hidden" aria-hidden="true">
        {Array.from({ length: 10 }).map((_, rowIndex) => (
          <div key={rowIndex} className="flex" style={{ marginTop: rowIndex === 0 ? '-80px' : '200px' }}>
            {Array.from({ length: 15 }).map((_, colIndex) => (
              <div key={colIndex} className="select-none text-foreground/[0.08] dark:text-foreground/[0.12]" style={{ width: '300px', marginLeft: colIndex === 0 ? (rowIndex % 2 === 0 ? '-50px' : '0') : '0', transform: 'rotate(-25deg)', transformOrigin: 'left center', fontSize: '12px', fontWeight: 500, whiteSpace: 'nowrap', padding: '30px 0' }}>
                {watermarkText}
              </div>
            ))}
          </div>
        ))}
      </div>
    )
  }

  return (
    <AppContext.Provider value={{ showAuthQrcode }}>
      {renderWatermark()}
      <div className="relative">
        {layoutContent}
      </div>
    </AppContext.Provider>
  )
}

export default BasicLayout
