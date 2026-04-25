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
import { createFetchTask, getFetchTask, updateFetchTask } from '@/api/fetchTask'
import type { FetchTaskCreate } from '@/types/fetchTask'
import CronExpressionPicker from '@/components/CronExpressionPicker'
import MpMultiSelect from '@/components/MpMultiSelect'

const formSchema = z.object({
  name: z.string().min(2, '任务名称长度应在 2-30 个字符之间').max(30),
  cron_exp: z.string().min(1, '请输入 cron 表达式'),
  max_page: z.union([z.number().int().min(1).max(50), z.nan()]).optional(),
  mps_id: z.array(z.any()).optional(),
  status: z.number(),
})

const FetchTaskForm: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [isEditMode, setIsEditMode] = useState(false)
  const [showCronPicker, setShowCronPicker] = useState(false)
  const [showMpSelector, setShowMpSelector] = useState(false)

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { name: '', cron_exp: '', max_page: undefined, mps_id: [], status: 1 },
  })

  useEffect(() => {
    if (id) {
      setIsEditMode(true)
      ;(async () => {
        setLoading(true)
        try {
          const res = await getFetchTask(id) as any
          form.reset({
            name: res.name,
            cron_exp: res.cron_exp,
            max_page: res.max_page ?? undefined,
            mps_id: JSON.parse(res.mps_id || '[]'),
            status: res.status,
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
      const submitData: FetchTaskCreate = {
        name: values.name,
        cron_exp: values.cron_exp,
        max_page: values.max_page && !Number.isNaN(values.max_page) ? Number(values.max_page) : null,
        mps_id: JSON.stringify(values.mps_id || []),
        status: values.status,
      }
      if (isEditMode && id) {
        await updateFetchTask(id, submitData)
        toast({ title: '成功', description: '更新成功，点击应用按钮使调度生效' })
      } else {
        await createFetchTask(submitData)
        toast({ title: '成功', description: '创建成功，点击应用按钮使调度生效' })
      }
      setTimeout(() => navigate('/fetch-tasks'), 1200)
    } catch (error: any) {
      toast({ variant: 'destructive', title: '错误', description: error?.message || '提交失败' })
    } finally {
      setLoading(false)
    }
  }

  const cronExp = form.watch('cron_exp')
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
        title={isEditMode ? '编辑抓取任务' : '添加抓取任务'}
        subTitle="按 cron 定时拉取指定公众号文章入库；不发任何消息"
        onBack={() => navigate(-1)}
      />

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>{isEditMode ? '编辑抓取任务' : '添加抓取任务'}</CardTitle>
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
                    <FormControl><Input placeholder="例如：科技公众号每日抓取" {...field} className="max-w-[600px]" /></FormControl>
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
                    <FormLabel>公众号</FormLabel>
                    <FormControl>
                      <div className="flex gap-2">
                        <Input
                          value={mpsId.map((mp: any) => mp.id?.toString() || '').join(',')}
                          placeholder="请选择公众号，留空对所有公众号生效"
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
                name="max_page"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>抓取页数</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
                        max={50}
                        placeholder="留空使用全局默认（max_page 配置）"
                        className="max-w-[300px]"
                        value={field.value ?? ''}
                        onChange={(e) => {
                          const v = e.target.value
                          field.onChange(v === '' ? undefined : Number(v))
                        }}
                      />
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
            <DialogDescription>选择要抓取的公众号，留空表示全部</DialogDescription>
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

export default FetchTaskForm
