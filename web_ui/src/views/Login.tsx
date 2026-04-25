import React, { useState, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import { login } from '@/api/auth'
import { useForm } from 'react-hook-form'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { User, Lock, Zap, Shield, Globe, CheckCircle, Activity } from 'lucide-react'

interface LoginFormData {
  username: string
  password: string
}

const Login: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()
  const form = useForm<LoginFormData>({
    defaultValues: {
      username: '',
      password: ''
    }
  })

  const appTitle = useMemo(
    () => import.meta.env.VITE_APP_TITLE || 'WeRSS 微信公众文章热度分析系统',
    []
  )

  const logo = useMemo(
    () => `${import.meta.env.BASE_URL}logo.svg`,
    []
  )

  const handleSubmit = async (values: LoginFormData) => {
    setLoading(true)
    try {
      const res = await login({
        username: values.username,
        password: values.password
      }) as any

      if (res?.access_token) {
        localStorage.setItem('token', res.access_token)
        const expiresIn = res.expires_in || 3600
        localStorage.setItem('token_expire', (Date.now() + (expiresIn * 1000)).toString())

        const redirect = searchParams.get('redirect')
        navigate(redirect || '/')
        toast({
          variant: "success",
          title: "登录成功",
          description: `欢迎进入控制台`
        })
      } else {
        throw new Error('无效的响应格式')
      }
    } catch (error: any) {
      console.error('登录错误:', error)
      const errorMsg = error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        '登录失败，请检查用户名和密码'
      toast({
        variant: "destructive",
        title: "登录失败",
        description: errorMsg
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-screen p-0 m-0 bg-background overflow-hidden font-sans">
      <div className="flex flex-col lg:flex-row h-full transition-all duration-300">
        {/* 左侧背景区域 */}
        <div className="hidden lg:flex flex-[0_0_60%] p-20 text-white flex-col justify-center bg-emerald-600 relative overflow-hidden">
          {/* 背景装饰光晕 */}
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-700 via-emerald-600 to-teal-800"></div>
          <div className="absolute -top-24 -right-24 w-[500px] h-[500px] bg-white/10 rounded-full blur-[100px] animate-pulse"></div>
          <div className="absolute -bottom-24 -left-24 w-[500px] h-[500px] bg-teal-400/20 rounded-full blur-[100px]"></div>
          
          <div className="relative z-10 max-w-[640px]">
            <div className="flex items-center gap-3 mb-8 animate-in fade-in slide-in-from-left-8 duration-700">
               <div className="bg-white/20 p-2.5 rounded-2xl backdrop-blur-md shadow-xl border border-white/30 flex items-center justify-center">
                  <img src={logo} alt="Logo" className="h-8 w-8 object-contain" />
               </div>
               <div className="h-8 w-px bg-white/30 mx-2"></div>
               <span className="text-xl font-medium tracking-[0.2em] opacity-90 uppercase">WeRSS Dashboard</span>
            </div>

            <h1 className="text-6xl mb-6 font-bold leading-tight drop-shadow-lg animate-in fade-in slide-in-from-left-12 duration-1000 delay-100">
               WeRSS 微信公众号热度分析系统
            </h1>
            
            <p className="text-xl leading-relaxed mb-12 opacity-80 max-w-[500px] animate-in fade-in slide-in-from-left-16 duration-1000 delay-300">
              专注于微信公众文章的自动采集、热度追踪、标签管理与多格式导出。
            </p>

            <div className="grid grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-500">
              <div className="flex flex-col gap-3 group">
                <div className="h-10 w-10 bg-white/10 rounded-xl flex items-center justify-center border border-white/20 group-hover:bg-white/20 transition-all">
                  <Zap className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-bold text-lg">自动采集</h4>
                  <p className="text-sm opacity-60">自动抓取全网微信公众号文章</p>
                </div>
              </div>

              <div className="flex flex-col gap-3 group">
                <div className="h-10 w-10 bg-white/10 rounded-xl flex items-center justify-center border border-white/20 group-hover:bg-white/20 transition-all">
                  <Globe className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-bold text-lg">热点分析</h4>
                  <p className="text-sm opacity-60">多维度追踪文章传播热度</p>
                </div>
              </div>

              <div className="flex flex-col gap-3 group">
                <div className="h-10 w-10 bg-white/10 rounded-xl flex items-center justify-center border border-white/20 group-hover:bg-white/20 transition-all">
                  <Shield className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-bold text-lg">标签系统</h4>
                  <p className="text-sm opacity-60">基于语义的内容分类与聚合</p>
                </div>
              </div>

              <div className="flex flex-col gap-3 group">
                <div className="h-10 w-10 bg-white/10 rounded-xl flex items-center justify-center border border-white/20 group-hover:bg-white/20 transition-all">
                  <CheckCircle className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-bold text-lg">标准输出</h4>
                  <p className="text-sm opacity-60">提供 RSS、Markdown、PDF</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 移动端顶部背景 */}
        <div className="lg:hidden h-48 bg-gradient-to-br from-emerald-600 to-teal-800 relative overflow-hidden flex items-center justify-center px-6">
          <div className="relative z-10 text-center">
            <h1 className="text-3xl font-bold text-white drop-shadow-md">{appTitle}</h1>
            <p className="text-white/60 text-sm mt-2 tracking-widest uppercase">WeRSS Heat Analysis</p>
          </div>
        </div>

        {/* 右侧登录区域 */}
        <div className="flex-1 flex justify-center items-center p-6 lg:p-20 bg-background relative">
          <div className="absolute top-10 right-10 text-muted-foreground text-sm hidden lg:block">
             Version 1.1.2
          </div>
          
          <Card className="w-full max-w-[460px] p-10 lg:p-12 bg-card rounded-[2rem] shadow-2xl shadow-primary/5 border-none animate-in zoom-in-95 duration-700">
            <div className="mb-10">
               <h2 className="text-3xl font-bold text-foreground">欢迎回来</h2>
               <p className="text-muted-foreground mt-2">请输入您的凭据以访问控制台</p>
            </div>

            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
                <FormField
                  control={form.control}
                  name="username"
                  render={({ field }) => (
                    <FormItem className="space-y-1">
                      <FormLabel className="text-xs font-bold uppercase tracking-widest text-muted-foreground ml-1">管理员账号</FormLabel>
                      <FormControl>
                        <div className="relative group">
                          <User className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500 transition-colors" />
                          <Input
                            placeholder="Account username"
                            className="pl-12 h-14 bg-muted border-border rounded-2xl focus:bg-card focus:ring-emerald-500/20 transition-all text-base"
                            autoComplete="username"
                            {...field}
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem className="space-y-1">
                      <FormLabel className="text-xs font-bold uppercase tracking-widest text-muted-foreground ml-1">访问密码</FormLabel>
                      <FormControl>
                        <div className="relative group">
                          <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-300 group-focus-within:text-emerald-500 transition-colors" />
                          <Input
                            type="password"
                            placeholder="Password"
                            className="pl-12 h-14 bg-muted border-border rounded-2xl focus:bg-card focus:ring-emerald-500/20 transition-all text-base"
                            autoComplete="current-password"
                            {...field}
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <Button 
                  type="submit" 
                  className="w-full h-14 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-lg font-bold shadow-lg shadow-emerald-200 transition-all hover:scale-[1.02] active:scale-[0.98]" 
                  disabled={loading}
                >
                  {loading ? (
                    <div className="flex items-center gap-2">
                       <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                       <span>验证中...</span>
                    </div>
                  ) : '进入系统'}
                </Button>
              </form>
            </Form>
            
            <div className="mt-12 pt-8 border-t border-border text-center">
               <p className="text-xs text-slate-300 font-medium">
                  © {new Date().getFullYear()} WeRSS. 版权所有.
               </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default Login
