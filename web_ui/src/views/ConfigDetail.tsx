import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Descriptions, DescriptionsItem } from '@/components/extensions/descriptions'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { PageHeader } from '@/components/extensions/page-header'
import { useToast } from '@/hooks/use-toast'
import {
  getConfig,
  updateConfig,
  deleteConfig
} from '@/api/configManagement'
import type { ConfigManagement } from '@/types/configManagement'
import { Edit, Trash2, Save, X } from 'lucide-react'
import { formatDateTime } from '@/utils/date'

interface FormValues {
  config_value: string
  description: string
}

const ConfigDetail: React.FC = () => {
  const { key } = useParams<{ key: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const [config, setConfig] = useState<ConfigManagement | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)

  const form = useForm<FormValues>({
    defaultValues: {
      config_value: '',
      description: ''
    }
  })

  const fetchConfig = async (configKey: string) => {
    try {
      setLoading(true)
      const res = await getConfig(configKey)
      const data = res.data || res
      setConfig(data)
      form.setValue('config_value', data.config_value)
      form.setValue('description', data.description || '')
    } catch (err: any) {
      setError(err instanceof Error ? err.message : '获取配置详情失败')
      toast({
        variant: "destructive",
        title: "错误",
        description: err instanceof Error ? err.message : '获取配置详情失败'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (key) {
      fetchConfig(key)
    }
  }, [key])

  const handleUpdate = async () => {
    try {
      setLoading(true)
      if (config) {
        const values = await form.trigger()
        if (!values) return
        
        const formValues = form.getValues()
        await updateConfig(config.config_key, formValues as any)
        await fetchConfig(key!)
        setIsEditing(false)
        toast({
          title: "成功",
          description: "配置更新成功"
        })
      }
    } catch (err: any) {
      setError(err instanceof Error ? err.message : '更新配置失败')
      toast({
        variant: "destructive",
        title: "错误",
        description: err instanceof Error ? err.message : '更新配置失败'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!config) return

    try {
      await deleteConfig(config.config_key)
      toast({
        title: "成功",
        description: "配置删除成功"
      })
      navigate('/configs')
    } catch (err: any) {
      setError(err instanceof Error ? err.message : '删除配置失败')
      toast({
        variant: "destructive",
        title: "错误",
        description: err instanceof Error ? err.message : '删除配置失败'
      })
    }
  }

  return (
    <div className="p-5">
      <PageHeader
        title={config ? `配置详情 - ${config.config_key}` : '配置详情'}
        onBack={() => navigate('/configs')}
        extra={
          <div className="flex gap-2">
            {!isEditing && (
              <>
                <Button onClick={() => setIsEditing(true)}>
                  <Edit className="h-4 w-4 mr-2" />
                  编辑
                </Button>
                <Button variant="destructive" onClick={() => setDeleteDialogOpen(true)}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  删除
                </Button>
              </>
            )}
            {isEditing && (
              <>
                <Button onClick={handleUpdate} disabled={loading}>
                  <Save className="h-4 w-4 mr-2" />
                  保存
                </Button>
                <Button variant="outline" onClick={() => setIsEditing(false)}>
                  <X className="h-4 w-4 mr-2" />
                  取消
                </Button>
              </>
            )}
          </div>
        }
      />

      <Card>
        <CardContent className="pt-6">
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {loading && !config ? (
            <div className="space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          ) : config ? (
            <>
              {!isEditing ? (
                <Descriptions column={1} bordered>
                  <DescriptionsItem label="配置键">
                    {config.config_key}
                  </DescriptionsItem>
                  <DescriptionsItem label="配置值">
                    {config.config_value}
                  </DescriptionsItem>
                  <DescriptionsItem label="描述">
                    {config.description || '-'}
                  </DescriptionsItem>
                  <DescriptionsItem label="创建时间">
                    {formatDateTime(config.created_at)}
                  </DescriptionsItem>
                  <DescriptionsItem label="更新时间">
                    {formatDateTime(config.updated_at)}
                  </DescriptionsItem>
                </Descriptions>
              ) : (
                <Form {...form}>
                  <form className="space-y-4">
                    <FormField
                      control={form.control}
                      name="config_value"
                      rules={{ required: '配置值不能为空' }}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>配置值</FormLabel>
                          <FormControl>
                            <Input {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="description"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>描述</FormLabel>
                          <FormControl>
                            <Textarea {...field} rows={4} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <div className="text-sm text-muted-foreground">
                      配置键: {config.config_key} (不可修改)
                    </div>
                  </form>
                </Form>
              )}
            </>
          ) : null}
        </CardContent>
      </Card>

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>确定要删除此配置吗？</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              取消
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default ConfigDetail
