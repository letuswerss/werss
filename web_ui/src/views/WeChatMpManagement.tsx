import React, { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'
import { Message } from '@/utils/message'
import { Modal } from '@/utils/modal'
import { Edit, Trash2, Plus, Upload as UploadIcon } from 'lucide-react'
import { getSubscriptions, addSubscription, updateSubscription, deleteSubscription, SubscriptionListResult } from '@/api/subscription'
import { getToken } from '@/utils/auth'
import { useTranslation } from 'react-i18next'

const formSchema = z.object({
  mp_id: z.string().optional().refine(
    (val) => !val || /^[a-zA-Z0-9_=-]+$/.test(val),
    { message: '公众号ID只能包含字母、数字、下划线、横线和等号' }
  ),
  mp_name: z.string().optional(),
  mp_cover: z.string().optional(),
  mp_intro: z.string().optional(),
  status: z.boolean(),
})

type FormValues = {
  mp_id?: string
  mp_name?: string
  mp_cover?: string
  mp_intro?: string
  status: boolean
}

interface Subscription {
  mp_id: string
  mp_name: string
  mp_cover: string
  mp_intro: string
  status: number
  sync_time: string | number
}

const WeChatMpManagement: React.FC = () => {
  const { t } = useTranslation()
  const [mpList, setMpList] = useState<Subscription[]>([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })
  const [visible, setVisible] = useState(false)
  const [modalTitle, setModalTitle] = useState('添加公众号')
  const [editingRecord, setEditingRecord] = useState<Subscription | null>(null)
  
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema) as any, // 类型兼容性处理
    defaultValues: {
      mp_id: '',
      mp_name: '',
      mp_cover: '',
      mp_intro: '',
      status: true,
    },
  })

  const loadData = async () => {
    try {
      const res = await getSubscriptions({
        page: pagination.current - 1,
        pageSize: pagination.pageSize
      }) as unknown as SubscriptionListResult

      const list = (res.list || res.data?.list || [])
      const total = res.total || res.data?.total || 0
      
      setMpList(list)
      setPagination(prev => ({ ...prev, total }))
    } catch (error: any) {
      console.error('获取公众号列表错误:', error)
      Message.error(error.message || t('wechatMp.messages.fetchFailed'))
    }
  }

  useEffect(() => {
    loadData()
  }, [pagination.current, pagination.pageSize])

  const showAddModal = () => {
    setModalTitle('添加公众号')
    setEditingRecord(null)
    form.reset({
      mp_id: '',
      mp_name: '',
      mp_cover: '',
      mp_intro: '',
      status: true,
    })
    setVisible(true)
  }

  const editMp = (record: Subscription) => {
    setModalTitle('编辑公众号')
    setEditingRecord(record)
    form.reset({
      mp_id: record.mp_id,
      mp_name: record.mp_name,
      mp_cover: record.mp_cover,
      mp_intro: record.mp_intro,
      status: record.status === 1,
    })
    setVisible(true)
  }

  const handleOk = async () => {
    try {
      const values = form.getValues()
      if (modalTitle === '添加公众号') {
        // 添加时需要 avatar 字段（使用 mp_cover 的值）
        const submitData = {
          mp_id: values.mp_id || '',
          mp_name: values.mp_name || '',
          avatar: values.mp_cover || '',
          mp_intro: values.mp_intro || '',
        }
        await addSubscription(submitData)
        Message.success(t('wechatMp.messages.addSuccess'))
      } else {
        // 更新时使用原有格式
        const submitData = {
          ...values,
          status: values.status ? 1 : 0
        }
        await updateSubscription(values.mp_id!, submitData)
        Message.success(t('wechatMp.messages.updateSuccess'))
      }
      setVisible(false)
      loadData()
    } catch (error: any) {
      console.error('保存失败:', error)
      Message.error(error.message || t('wechatMp.messages.saveFailed'))
    }
  }

  const deleteMp = async (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个公众号吗？',
      onOk: async () => {
        try {
          await deleteSubscription(id)
          Message.success(t('wechatMp.messages.deleteSuccess'))
          loadData()
        } catch (error: any) {
          console.error('删除失败:', error)
          Message.error(error.message || t('wechatMp.messages.deleteFailed'))
        }
      }
    })
  }

  const handlePageChange = (page: number) => {
    setPagination(prev => ({ ...prev, current: page }))
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/wx/mps/upload', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${getToken()}`
        },
        body: formData
      })
      const result = await response.json()
      const url = result?.data?.url || result?.url || result?.url
      if (url) {
        form.setValue('mp_cover', url)
        Message.success(t('wechatMp.messages.uploadSuccess'))
      }
    } catch (error) {
      Message.error(t('wechatMp.messages.uploadFailed'))
    }
  }

  const totalPages = Math.ceil(pagination.total / pagination.pageSize)

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 text-foreground">
          公众号管理
        </h1>
        <p className="text-muted-foreground text-sm">
          管理微信公众号信息
        </p>
      </div>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>公众号列表</CardTitle>
          <Button onClick={showAddModal}>
            <Plus className="mr-2 h-4 w-4" />
            添加公众号
          </Button>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>公众号ID</TableHead>
                  <TableHead>名称</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>最后同步</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mpList.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground">
                      暂无数据
                    </TableCell>
                  </TableRow>
                ) : (
                  mpList.map((record) => (
                    <TableRow key={record.mp_id}>
                      <TableCell>{record.mp_id}</TableCell>
                      <TableCell>{record.mp_name}</TableCell>
                      <TableCell>
                        <Badge variant={record.status === 1 ? 'secondary' : 'destructive'}>
                          {record.status === 1 ? '已启用' : '已禁用'}
                        </Badge>
                      </TableCell>
                      <TableCell>{record.sync_time || '-'}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" onClick={() => editMp(record)}>
                            <Edit className="h-4 w-4 mr-1" />
                            编辑
                          </Button>
                          <Button size="sm" variant="destructive" onClick={() => deleteMp(record.mp_id)}>
                            <Trash2 className="h-4 w-4 mr-1" />
                            删除
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
          {totalPages > 1 && (
            <div className="mt-4">
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      href="#"
                      onClick={(e) => {
                        e.preventDefault()
                        if (pagination.current > 1) {
                          handlePageChange(pagination.current - 1)
                        }
                      }}
                      className={pagination.current <= 1 ? 'pointer-events-none opacity-50' : ''}
                    />
                  </PaginationItem>
                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                    let pageNum: number
                    if (totalPages <= 5) {
                      pageNum = i + 1
                    } else if (pagination.current <= 3) {
                      pageNum = i + 1
                    } else if (pagination.current >= totalPages - 2) {
                      pageNum = totalPages - 4 + i
                    } else {
                      pageNum = pagination.current - 2 + i
                    }
                    return (
                      <PaginationItem key={pageNum}>
                        <PaginationLink
                          href="#"
                          onClick={(e) => {
                            e.preventDefault()
                            handlePageChange(pageNum)
                          }}
                          isActive={pagination.current === pageNum}
                        >
                          {pageNum}
                        </PaginationLink>
                      </PaginationItem>
                    )
                  })}
                  <PaginationItem>
                    <PaginationNext
                      href="#"
                      onClick={(e) => {
                        e.preventDefault()
                        if (pagination.current < totalPages) {
                          handlePageChange(pagination.current + 1)
                        }
                      }}
                      className={pagination.current >= totalPages ? 'pointer-events-none opacity-50' : ''}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={visible} onOpenChange={setVisible}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{modalTitle}</DialogTitle>
            <DialogDescription>
              {editingRecord ? '修改公众号的基本信息' : '添加一个新的公众号'}
            </DialogDescription>
          </DialogHeader>
          {visible && form?.control && (
            <Form {...form}>
              <form className="space-y-4">
              <FormField
                control={form.control}
                name="mp_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>公众号ID</FormLabel>
                    <FormControl>
                      <Input {...field} disabled={!!editingRecord} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="mp_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>公众号名称</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="mp_cover"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>封面图</FormLabel>
                    <FormControl>
                      <div className="space-y-2">
                        <Input {...field} placeholder="图片URL" />
                        <div className="relative">
                          <input
                            type="file"
                            accept="image/*"
                            onChange={handleFileUpload}
                            className="hidden"
                            id="upload-cover"
                          />
                          <Button
                            type="button"
                            variant="outline"
                            onClick={() => document.getElementById('upload-cover')?.click()}
                          >
                            <UploadIcon className="h-4 w-4 mr-2" />
                            上传图片
                          </Button>
                        </div>
                        {field.value && (
                          <img src={field.value} alt="封面" className="w-32 h-32 object-cover rounded" />
                        )}
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="mp_intro"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>简介</FormLabel>
                    <FormControl>
                      <Textarea {...field} rows={4} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="status"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
                    <div className="space-y-0.5">
                      <FormLabel>状态</FormLabel>
                    </div>
                    <FormControl>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                  </FormItem>
                )}
              />
              </form>
            </Form>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setVisible(false)}>取消</Button>
            <Button onClick={handleOk}>确定</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default WeChatMpManagement
