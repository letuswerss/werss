import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '@/components/extensions/page-header'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Upload } from '@/components/extensions/upload'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { useToast } from '@/hooks/use-toast'
import { getUserInfo, updateUserInfo, uploadAvatar } from '@/api/user'
import { useForm } from 'react-hook-form'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { User, Mail, Edit } from 'lucide-react'

interface FormData {
  nickname: string
  email: string
  avatar: string
}

const EditUser: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [username, setUsername] = useState('')
  const { toast } = useToast()
  const form = useForm<FormData>({
    defaultValues: {
      nickname: '',
      email: '',
      avatar: ''
    }
  })

  const fetchUserInfo = async () => {
    setLoading(true)
    try {
      const res = await getUserInfo()
      const userData = (res as any).data || res
      setUsername(userData.username || '')
      form.reset({
        nickname: userData.nickname || userData.username,
        email: userData.email || '',
        avatar: userData.avatar || ''
      })
    } catch (error) {
      navigate('/login')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUserInfo()
  }, [])

  const handleUploadChange = async (fileList: File[]) => {
    const file = fileList[0]

    if (!file?.type?.startsWith('image/')) {
      toast({
        variant: "destructive",
        title: "错误",
        description: '请选择图片文件 (JPEG/PNG)'
      })
      return false
    }

    if (file.size > 2 * 1024 * 1024) {
      toast({
        variant: "destructive",
        title: "错误",
        description: '图片大小不能超过2MB'
      })
      return false
    }

    try {
      const res = await uploadAvatar(file)
      const avatarUrl = (res as any).url || (res as any).avatar || (res as any).data?.avatar
      form.setValue('avatar', avatarUrl)
    } catch (error: any) {
      console.error('上传错误:', error)
      toast({
        variant: "destructive",
        title: "上传失败",
        description: error.response?.data?.message || error.message || '服务器错误'
      })
    }
    return false
  }

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.target as HTMLImageElement
    img.src = '/default-avatar.png'
  }

  const handleSubmit = async (values: FormData) => {
    setLoading(true)
    try {
      const response = await updateUserInfo(values)
      if ((response as any).code === 0) {
        toast({
          title: "成功",
          description: (response as any)?.message || '更新成功'
        })
      }
    } catch (error) {
      console.error('更新失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    fetchUserInfo()
  }

  const goBack = () => {
    navigate(-1)
  }

  return (
    <div className="p-5 max-w-[600px] mx-auto">
      <PageHeader
        title="修改个人信息"
        subTitle="更新您的账户信息"
        onBack={goBack}
      />

      <Card>
        <CardContent className="p-6">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-5">
              <div className="space-y-2">
                <FormLabel>用户名</FormLabel>
                <Input
                  value={username}
                  readOnly
                  disabled
                  className="bg-muted/50"
                />
                <p className="text-xs text-muted-foreground">
                  用户名用于登录和系统识别，不支持修改
                </p>
              </div>

              <FormField
                control={form.control}
                name="avatar"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>头像</FormLabel>
                    <FormControl>
                      <Upload
                        customRequest={handleUploadChange}
                        accept="image/*"
                        limit={1}
                      >
                        <div className="relative w-20 h-20 cursor-pointer group">
                          <Avatar className="w-20 h-20">
                            {field.value ? (
                              <AvatarImage
                                src={field.value}
                                alt="avatar"
                                onError={handleImageError}
                              />
                            ) : (
                              <AvatarFallback>
                                <User className="h-10 w-10" />
                              </AvatarFallback>
                            )}
                          </Avatar>
                          <div className="absolute top-0 left-0 w-full h-full bg-black/50 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                            <Edit className="h-5 w-5 text-white" />
                          </div>
                        </div>
                      </Upload>
                    </FormControl>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="nickname"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>昵称</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          placeholder="请输入昵称"
                          className="pl-9"
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
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>邮箱</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          type="email"
                          placeholder="请输入邮箱"
                          className="pl-9"
                          {...field}
                        />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex gap-2">
                <Button type="submit" disabled={loading}>
                  {loading ? '保存中...' : '保存修改'}
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

export default EditUser
