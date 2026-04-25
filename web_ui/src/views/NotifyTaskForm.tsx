import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { PageHeader } from '@/components/extensions/page-header'
import { useToast } from '@/hooks/use-toast'
import { createNotifyTask, getNotifyTask, updateNotifyTask } from '@/api/notifyTask'
import type { NotifyTaskCreate } from '@/types/notifyTask'
import CronExpressionPicker from '@/components/CronExpressionPicker'
import MpMultiSelect from '@/components/MpMultiSelect'
import ACodeEditor from '@/components/ACodeEditor'

const formSchema = z.object({
  name: z.string().min(2, '任务名称长度应在 2-30 个字符之间').max(30),
  message_type: z.number(),
  message_template: z.string().optional(),
  web_hook_url: z.string().min(1, '请填写 webhook 地址'),
  mps_id: z.array(z.any()).optional(),
  status: z.number(),
  cron_exp: z.string().min(1, '请输入 cron 表达式'),
})

const NotifyTaskForm: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [isEditMode, setIsEditMode] = useState(false)
  const [showCronPicker, setShowCronPicker] = useState(false)
  const [showMpSelector, setShowMpSelector] = useState(false)

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      message_type: 0,
      message_template: '',
      web_hook_url: '',
      mps_id: [],
      status: 1,
      cron_exp: '',
    },
  })

  useEffect(() => {
    if (id) {
      setIsEditMode(true)
      ;(async () => {
        setLoading(true)
        try {
          const res = await getNotifyTask(id) as any
          form.reset({
            name: res.name,
            message_type: res.message_type,
            message_template: res.message_template,
            web_hook_url: res.web_hook_url,
            mps_id: JSON.parse(res.mps_id || '[]'),
            status: res.status,
            cron_exp: res.cron_exp,
          })
        } finally {
          setLoading(false)
        }
      })()
    }
  }, [id])

  const handleSubmit = async (values: z.infer<typeof formSchema>) => {
    setLoading(true)
    try {
      const submitData: NotifyTaskCreate = {
        name: values.name,
        message_type: values.message_type,
        message_template: values.message_template || '',
        web_hook_url: values.web_hook_url,
        mps_id: JSON.stringify(values.mps_id || []),
        status: values.status,
        cron_exp: values.cron_exp,
      }
      if (isEditMode && id) {
        await updateNotifyTask(id, submitData)
        toast({ title: '成功', description: '更新成功，点击应用按钮使调度生效' })
      } else {
        await createNotifyTask(submitData)
        toast({ title: '成功', description: '创建成功，点击应用按钮使调度生效' })
      }
      setTimeout(() => navigate('/notify-tasks'), 1200)
    } catch (error: any) {
      toast({ variant: 'destructive', title: '错误', description: error?.message || '提交失败' })
    } finally {
      setLoading(false)
    }
  }

  const cronExp = form.watch('cron_exp')
  const messageType = form.watch('message_type')
  const mpsId = form.watch('mps_id') || []

  if (loading && !form.formState.isDirty) {
    return (
      <div className="p-6 max-w-[1200px] mx-auto">
        <Skeleton className="h-8 w-48 mb-6" />
        <Card>
          <CardHeader><Skeleton className="h-6 w-32" /></CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      <PageHeader
        title={isEditMode ? '编辑推送任务' : '添加推送任务'}
        subTitle="按 cron 把数据库里的文章渲染推到 webhook；不做任何抓取"
        onBack={() => navigate(-1)}
      />

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>{isEditMode ? '编辑推送任务' : '添加推送任务'}</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>任务名称 <span className="text-destructive">*</span></FormLabel>
                    <FormControl><Input placeholder="例如：每日聚合早报" {...field} className="max-w-[600px]" /></FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="message_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>消息类型</FormLabel>
                    <FormControl>
                      <Select value={field.value?.toString()} onValueChange={(v) => field.onChange(parseInt(v))}>
                        <SelectTrigger className="w-[200px]"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">Message（Markdown）</SelectItem>
                          <SelectItem value="1">WebHook（结构化）</SelectItem>
                        </SelectContent>
                      </Select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="message_template"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>消息模板</FormLabel>
                    <FormControl>
                      <div>
                        <ACodeEditor
                          value={field.value || ''}
                          onChange={(value) => field.onChange(value)}
                          placeholder="请输入消息模板内容"
                          language="custom"
                        />
                        {messageType === 0 ? (
                          <div className="mt-2 flex gap-2">
                            <Button
                              type="button"
                              variant="outline"
                              onClick={() => {
                                form.setValue('message_template', '{{ today }} 每日科技聚合资讯\n\n{% for item in feeds_with_articles %}\n## {{ item.feed.mp_name }}\n\n{% for article in item.articles %}\n- [**{{ article.title }}**]({{ article.url }}){% if article.tag_names %} 🏷️ {{= \', \'.join(article.tag_names) if isinstance(article.tag_names, list) else str(article.tag_names) }}{% endif %}\n{% endfor %}\n\n{% endfor %}\n\n---\n📊 共 {{ total_articles }} 篇文章，来自 {{ feeds_count }} 个公众号')
                              }}
                            >
                              使用聚合 Markdown 模板
                            </Button>
                          </div>
                        ) : (
                          <Button
                            type="button"
                            variant="outline"
                            className="mt-2"
                            onClick={() => form.setValue('message_template', '{\n    "articles": [\n    {% for article in articles %}\n    {{article}}\n    {% if not loop.last %},{% endif %}\n    {% endfor %}\n    ]\n}')}
                          >
                            使用 WebHook 模板
                          </Button>
                        )}
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="web_hook_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>WebHook 地址 <span className="text-destructive">*</span></FormLabel>
                    <FormControl>
                      <div className="space-y-2 max-w-[700px]">
                        <Input placeholder="钉钉/飞书/企业微信/自定义 URL" {...field} />
                        <a
                          href="https://open.dingtalk.com/document/orgapp/obtain-the-webhook-address-of-a-custom-robot"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-primary hover:underline"
                        >
                          如何获取 WebHook
                        </a>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="cron_exp"
                render={() => (
                  <FormItem>
                    <FormLabel>cron 表达式 <span className="text-destructive">*</span></FormLabel>
                    <FormControl>
                      <div className="flex gap-2">
                        <Input value={cronExp || ''} placeholder="点击右侧按钮选择" readOnly className="flex-1 max-w-[500px]" />
                        <Button type="button" onClick={() => setShowCronPicker(true)}>选择</Button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="mps_id"
                render={() => (
                  <FormItem>
                    <FormLabel>数据来源公众号</FormLabel>
                    <FormControl>
                      <div className="flex gap-2">
                        <Input
                          value={mpsId.map((mp: any) => mp.id?.toString() || '').join(',')}
                          placeholder="留空 = 所有公众号"
                          readOnly
                          className="flex-1 max-w-[500px]"
                        />
                        <Button type="button" onClick={() => setShowMpSelector(true)}>选择</Button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="status"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>状态</FormLabel>
                    <FormControl>
                      <Select value={field.value?.toString()} onValueChange={(v) => field.onChange(parseInt(v))}>
                        <SelectTrigger className="w-[200px]"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1">启用</SelectItem>
                          <SelectItem value="0">禁用</SelectItem>
                        </SelectContent>
                      </Select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex gap-2 pt-4">
                <Button type="submit" disabled={loading}>{loading ? '提交中...' : '提交'}</Button>
                <Button type="button" variant="outline" onClick={() => navigate(-1)}>取消</Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>

      <Dialog open={showCronPicker} onOpenChange={setShowCronPicker}>
        <DialogContent className="max-w-[800px] max-h-[90vh] flex flex-col">
          <DialogHeader className="flex-shrink-0">
            <DialogTitle>选择 cron 表达式</DialogTitle>
            <DialogDescription>选择或自定义任务执行的 cron 表达式</DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto min-h-0 px-1">
            <CronExpressionPicker value={cronExp || ''} onChange={(v) => form.setValue('cron_exp', v)} />
          </div>
          <DialogFooter className="flex-shrink-0">
            <Button onClick={() => setShowCronPicker(false)}>确定</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showMpSelector} onOpenChange={setShowMpSelector}>
        <DialogContent className="max-w-[800px]">
          <DialogHeader>
            <DialogTitle>选择公众号</DialogTitle>
            <DialogDescription>选择推送数据来源的公众号，留空表示全部</DialogDescription>
          </DialogHeader>
          <MpMultiSelect value={mpsId} onChange={(v) => form.setValue('mps_id', v)} />
          <DialogFooter>
            <Button onClick={() => setShowMpSelector(false)}>确定</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default NotifyTaskForm
