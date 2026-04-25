import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { PageHeader } from '@/components/extensions/page-header'
import { useToast } from '@/hooks/use-toast'
import { changePassword } from '@/api/user'
import { Lock } from 'lucide-react'

interface FormValues {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

const ChangePassword: React.FC = () => {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)

  const form = useForm<FormValues>({
    defaultValues: {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    },
    mode: 'onChange'
  })

  const validatePassword = (value: string) => {
    if (!value) {
      return '请输入密码'
    }
    if (value.length < 8) {
      return '密码长度不能少于8位'
    }
    if (value.length > 20) {
      return '密码长度不能超过20位'
    }
    if (!/[a-z]/.test(value)) {
      return '必须包含至少一个小写字母'
    }
    if (!/[0-9]/.test(value)) {
      return '必须包含至少一个数字'
    }
    if (!/[^A-Za-z0-9]/.test(value)) {
      return '必须包含至少一个特殊字符'
    }
    return undefined
  }

  const onSubmit = async (values: FormValues) => {
    if (values.newPassword !== values.confirmPassword) {
      toast({
        variant: "destructive",
        title: "错误",
        description: "新密码与确认密码不一致"
      })
      return
    }

    setLoading(true)
    try {
      const response = await changePassword({
        old_password: values.currentPassword,
        new_password: values.newPassword
      })
      console.log(response)
      if ((response as any).code === 0) {
        toast({
          title: "成功",
          description: "密码修改成功"
        })
        localStorage.removeItem('token')
        setTimeout(() => {
          navigate('/login')
        }, 1500)
      } else {
        toast({
          variant: "destructive",
          title: "错误",
          description: `密码修改失败: ${(response as any).data?.message || '未知错误'}`
        })
      }
    } catch (error: any) {
      console.error('修改密码失败:', error)
      toast({
        variant: "destructive",
        title: "错误",
        description: error.message || '修改密码失败'
      })
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    form.reset()
  }

  const goBack = () => {
    navigate(-1)
  }

  return (
    <div className="p-5 max-w-[600px] mx-auto">
      <PageHeader
        title="修改密码"
        subTitle="定期修改密码有助于账户安全"
        onBack={goBack}
      />

      <Card>
        <CardHeader>
          <CardTitle>修改密码</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="currentPassword"
                rules={{
                  validate: validatePassword
                }}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>当前密码</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          {...field}
                          type="password"
                          placeholder="请输入当前密码"
                          className="pl-10"
                        />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="newPassword"
                rules={{
                  validate: validatePassword
                }}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>新密码</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          {...field}
                          type="password"
                          placeholder="请输入新密码"
                          className="pl-10"
                        />
                      </div>
                    </FormControl>
                    <FormDescription>
                      密码长度8-20位，必须包含小写字母、数字和特殊字符
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="confirmPassword"
                rules={{
                  validate: (value) => {
                    if (!value) {
                      return '请确认密码'
                    }
                    if (value !== form.getValues('newPassword')) {
                      return '两次输入的密码不一致'
                    }
                    return undefined
                  }
                }}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>确认新密码</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          {...field}
                          type="password"
                          placeholder="请再次输入新密码"
                          className="pl-10"
                        />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex gap-2">
                <Button type="submit" disabled={loading}>
                  {loading ? '修改中...' : '确认修改'}
                </Button>
                <Button type="button" variant="outline" onClick={resetForm}>
                  重置
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  )
}

export default ChangePassword
