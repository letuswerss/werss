import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Message } from '@/utils/message'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Plus, Edit, Trash2, RefreshCw, Search, Loader2 } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { getSubscriptions, deleteSubscription, updateSubscription, SubscriptionListResult, Subscription, UpdateMps } from '@/api/subscription'
import { formatDateTime, formatTimestamp } from '@/utils/date'
import { Avatar as AvatarUtil } from '@/utils/constants'
import dayjs from 'dayjs'

const SubscriptionManagement: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { id } = useParams<{ id?: string }>()
  const [loading, setLoading] = useState(false)
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [selectedSubscription, setSelectedSubscription] = useState<Subscription | null>(null)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })
  const [searchText, setSearchText] = useState('')
  const [visible, setVisible] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null)
  const [jumpPageInput, setJumpPageInput] = useState('1')

  const form = useForm({
    defaultValues: {
      mp_id: '',
      mp_name: '',
      mp_intro: '',
      status: true
    }
  })

  // 加载订阅列表
  const loadSubscriptions = async () => {
    setLoading(true)
    try {
      const res = await getSubscriptions({
        page: pagination.current - 1,
        pageSize: pagination.pageSize,
        kw: searchText
      }) as unknown as SubscriptionListResult

      const list = res.list || res.data?.list || []
      const total = res.total || res.data?.total || 0

      setSubscriptions(list)
      setPagination(prev => ({ ...prev, total }))

      // 如果有选中的订阅，更新选中状态
      if (id && list.length > 0) {
        const found = list.find(item => item.mp_id === id)
        if (found) {
          setSelectedSubscription(found)
        }
      } else if (list.length > 0 && !selectedSubscription) {
        // 默认选中第一个
        setSelectedSubscription(list[0])
        navigate(`/subscriptions/${list[0].mp_id}`, { replace: true })
      }
    } catch (error: any) {
      console.error('获取订阅列表失败:', error)
      Message.error(error.message || t('subscriptions.messages.fetchFailed'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSubscriptions()
  }, [pagination.current, pagination.pageSize, searchText])

  useEffect(() => {
    setJumpPageInput(String(pagination.current))
  }, [pagination.current])

  // 选择订阅
  const handleSelectSubscription = (subscription: Subscription) => {
    setSelectedSubscription(subscription)
    navigate(`/subscriptions/${subscription.mp_id}`)
  }

  // 刷新订阅（更新文章）
  const handleRefresh = async () => {
    if (!selectedSubscription) {
      Message.warning(t('subscriptions.messages.selectFirst'))
      return
    }
    setRefreshing(true)
    try {
      await UpdateMps(selectedSubscription.mp_id, {
        start_page: 0,
        end_page: 1
      })
      
      Message.success(t('subscriptions.messages.refreshSuccess'))
      
      setTimeout(() => {
        loadSubscriptions()
      }, 2000)
    } catch (error: any) {
      console.error('刷新失败:', error)
      let errorData: any = null
      
      if (typeof error === 'string') {
        Message.error(error || t('subscriptions.messages.refreshFailed'))
        return
      }
      
      if (error && typeof error === 'object' && 'code' in error) {
        errorData = error
      } else if (error?.response?.data) {
        errorData = error.response.data.detail || error.response.data
      } else {
        errorData = error
      }
      
      if (errorData?.code === 40402) {
        const timeSpan = errorData?.data?.time_span || 0
        const syncInterval = 60
        const remaining = Math.max(0, syncInterval - timeSpan)
        Message.warning(t('subscriptions.messages.refreshLimit', { seconds: remaining }))
      } else {
        const errorMsg = errorData?.message || error?.message || t('subscriptions.messages.refreshFailed')
        Message.error(errorMsg)
      }
    } finally {
      setRefreshing(false)
    }
  }

  // 删除订阅
  const handleDelete = async (mpId: string) => {
    try {
      await deleteSubscription(mpId)
      Message.success('删除成功')
      if (selectedSubscription?.mp_id === mpId) {
        setSelectedSubscription(null)
        navigate('/subscriptions', { replace: true })
      }
      loadSubscriptions()
    } catch (error: any) {
      Message.error(error.message || '删除失败')
    }
  }

  // 编辑订阅
  const handleEdit = (subscription: Subscription) => {
    form.reset({
      ...subscription,
      status: subscription.status === 1
    })
    setVisible(true)
  }

  // 保存编辑
  const handleSave = async () => {
    try {
      const values = form.getValues()
      await updateSubscription(values.mp_id, {
        ...values,
        status: values.status ? 1 : 0
      })
      Message.success('保存成功')
      setVisible(false)
      loadSubscriptions()
      if (selectedSubscription?.mp_id === values.mp_id) {
        const updated = subscriptions.find(s => s.mp_id === values.mp_id)
        if (updated) {
          setSelectedSubscription(updated)
        }
      }
    } catch (error: any) {
      Message.error(error.message || '保存失败')
    }
  }

  const subscriptionColumns: Array<{
    title: string
    dataIndex?: string
    ellipsis?: boolean
    width?: number
    align?: 'center' | 'left' | 'right'
    render?: (value: any, record: Subscription) => React.ReactNode
  }> = [
    {
      title: t('subscriptions.columns.name'),
      dataIndex: 'mp_name',
      ellipsis: true,
      render: (text: string, record: Subscription) => (
        <div
          className={`cursor-pointer font-medium transition-all ${
            selectedSubscription?.mp_id === record.mp_id ? 'text-primary font-semibold' : 'text-foreground'
          }`}
          onClick={() => handleSelectSubscription(record)}
        >
          {text || record.mp_id}
        </div>
      )
    },
    {
      title: t('subscriptions.columns.articleCount'),
      dataIndex: 'article_count',
      width: 80,
      align: 'center',
      render: (count: number) => (
        <span className="font-medium text-foreground">{count || 0}</span>
      )
    },
    {
      title: t('subscriptions.columns.status'),
      dataIndex: 'status',
      width: 80,
      align: 'center',
      render: (status: number) => (
        <Badge variant={status === 1 ? 'default' : 'destructive'} className="rounded px-1.5 py-0.5 text-[10px]">
          <span className="dark:text-dark whitespace-nowrap">{status === 1 ? t('common.enabled') : t('common.disabled')}</span>
        </Badge>
      )
    }
  ]

  const renderPagination = () => {
    const totalPages = Math.ceil(pagination.total / pagination.pageSize)
    const handleJumpPage = () => {
      const targetPage = Number.parseInt(jumpPageInput, 10)
      if (Number.isNaN(targetPage)) {
        setJumpPageInput(String(pagination.current))
        return
      }

      const nextPage = Math.min(Math.max(targetPage, 1), Math.max(1, totalPages))
      setPagination(prev => ({ ...prev, current: nextPage }))
      setJumpPageInput(String(nextPage))
    }

    return (
      <div className="flex items-center justify-center mt-4 pb-2">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>{t('common.gotoPage')}</span>
            <Input
              type="number"
              min={1}
              max={totalPages}
              value={jumpPageInput}
              onChange={(e) => setJumpPageInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleJumpPage()
                }
              }}
              onBlur={handleJumpPage}
              className="h-8 w-20"
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPagination(prev => ({ ...prev, current: Math.max(1, prev.current - 1) }))}
            disabled={pagination.current === 1}
          >
            上一页
          </Button>
          <span className="text-xs text-muted-foreground">
            {pagination.current} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPagination(prev => ({ ...prev, current: Math.min(totalPages, prev.current + 1) }))}
            disabled={pagination.current >= totalPages}
          >
            下一页
          </Button>
        </div>
      </div>
    )
  }

  return (
    // 修改 1: 根容器改为 h-screen 和 flex-col，确保页面占满且不出现滚动条
    <div className="h-screen w-full flex flex-col overflow-hidden bg-background">
      
      {/* 头部区域：固定高度 */}
      <div className="flex-shrink-0 p-6 pb-4">
        <h1 className="text-3xl font-bold mb-2 text-foreground">
          {t('subscriptions.title')}
        </h1>
        <p className="text-muted-foreground text-sm">
          {t('subscriptions.subtitle')}
        </p>
      </div>
      
      {/* 主内容区域：flex-1 自动填充剩余空间，min-h-0 防止子元素溢出 */}
      <div className="flex-1 min-h-0 flex gap-6 px-6 pb-6">
        
        {/* 左侧：订阅列表 - 保持 flex 结构 */}
        <div className="w-[450px] rounded-lg border bg-white shadow-sm dark:bg-background flex flex-col flex-shrink-0 overflow-hidden">
          {/* 搜索和添加按钮区域 */}
          <div className="p-4 border-b flex-shrink-0">
            <div className="flex gap-3 mb-3">
              <div className="relative flex-1">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={t('subscriptions.searchPlaceholder')}
                  value={searchText}
                  onChange={(e) => {
                    setSearchText(e.target.value)
                    setPagination(prev => ({ ...prev, current: 1 }))
                  }}
                  className="pl-8"
                />
              </div>
            </div>
            <Button
              className="w-full"
              onClick={() => navigate('/add-subscription')}
            >
              <Plus className="h-4 w-4 mr-2" />
              {t('subscriptions.addSubscription')}
            </Button>
          </div>
          
          {/* 表格区域：flex-1 自动撑开 */}
          <div className="flex-1 overflow-auto p-2">
            <div className="rounded-md border overflow-hidden bg-card">
              <Table>
                <TableHeader className="sticky top-0 z-10 bg-card shadow-sm">
                  <TableRow>
                    {subscriptionColumns.map((column, index) => (
                      <TableHead
                        key={column.dataIndex || index}
                        style={column.width ? { width: column.width } : undefined}
                        className={column.align === 'center' ? 'text-center' : ''}
                      >
                        {column.title}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={subscriptionColumns.length} className="h-24 text-center">
                        <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                      </TableCell>
                    </TableRow>
                  ) : subscriptions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={subscriptionColumns.length} className="h-24 text-center text-muted-foreground">
                        {t('common.noData')}
                      </TableCell>
                    </TableRow>
                  ) : (
                    subscriptions.map((record) => (
                      <TableRow
                        key={record.mp_id}
                        className={`cursor-pointer transition-all ${
                          selectedSubscription?.mp_id === record.mp_id
                            ? 'bg-primary/10 border-l-4 border-l-primary'
                            : 'hover:bg-muted/50'
                        }`}
                        onClick={() => handleSelectSubscription(record)}
                      >
                        {subscriptionColumns.map((column, colIndex) => {
                          const value = column.dataIndex ? record[column.dataIndex as keyof Subscription] : undefined
                          const content = column.render
                            ? column.render(value as any, record)
                            : value
                          return (
                            <TableCell
                              key={column.dataIndex || colIndex}
                              className={column.align === 'center' ? 'text-center' : ''}
                            >
                              {content}
                            </TableCell>
                          )
                        })}
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
            {/* 分页组件，放在 flex 容器内，跟随滚动区域底部 */}
            {renderPagination()}
          </div>
        </div>

        {/* 右侧：订阅详情 */}
        <div className="flex-1 min-w-[500px] flex flex-col h-full overflow-hidden">
          {selectedSubscription ? (
            <Card className="rounded-lg border bg-white shadow-sm dark:bg-background flex flex-col h-full overflow-hidden">
              <CardHeader className="flex-shrink-0 pb-4 pt-6 px-6 border-b">
                <div className="flex md:flex-row flex-col items-center gap-4 flex-1 min-w-0 w-full">
                  <div className="flex items-center gap-4 flex-1 min-w-0 w-full">
                    <Avatar className="h-14 w-14 rounded-full flex-shrink-0 border">
                      {(selectedSubscription as any).mp_cover || (selectedSubscription as any).avatar ? (
                        <AvatarImage 
                          src={AvatarUtil((selectedSubscription as any).mp_cover || (selectedSubscription as any).avatar)} 
                          alt={selectedSubscription.mp_name || selectedSubscription.mp_id}
                        />
                      ) : (
                        <AvatarFallback className="bg-primary/10 text-primary text-xl font-bold rounded-lg">
                          {(selectedSubscription.mp_name || selectedSubscription.mp_id).charAt(0).toUpperCase()}
                        </AvatarFallback>
                      )}
                    </Avatar>
                    <div className="min-w-0 flex-1">
                      <div className="text-xl font-bold text-foreground mb-1 truncate" title={selectedSubscription.mp_name}>
                        {selectedSubscription.mp_name || selectedSubscription.mp_id}
                      </div>
                      <div className="text-xs text-muted-foreground truncate font-mono">
                        ID: {selectedSubscription.mp_id}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleRefresh}
                      disabled={refreshing}
                    >
                      {refreshing ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4 mr-2" />
                      )}
                      {t('subscriptions.refresh')}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEdit(selectedSubscription)}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      {t('subscriptions.edit')}
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => {
                        setDeleteTargetId(selectedSubscription.mp_id)
                        setDeleteDialogOpen(true)
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="flex-1 overflow-y-auto p-6">
                <div className="grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-5 w-full box-border">
                  {/* 状态卡片 */}
                  <div className="rounded-lg border bg-white p-4 dark:bg-muted/30">
                    <div className="text-muted-foreground text-xs mb-2 font-semibold">
                      {t('subscriptions.details.status')}
                    </div>
                    <div>
                      <Badge 
                        variant={selectedSubscription.status === 1 ? 'default' : 'destructive'}
                        className="text-sm px-3 py-1 rounded-md font-medium"
                      >
                        <span className="dark:text-foreground whitespace-nowrap">{selectedSubscription.status === 1 ? t('common.enabled') : t('common.disabled')}</span>
                      </Badge>
                    </div>
                  </div>

                  {/* 文章数量卡片 */}
                  <div className="rounded-lg border bg-white p-4 dark:bg-muted/30">
                    <div className="text-muted-foreground text-xs mb-2 font-semibold">
                      {t('subscriptions.details.articleCount')}
                    </div>
                    <div className="text-2xl font-bold text-foreground leading-none">
                      {selectedSubscription.article_count || 0}
                    </div>
                  </div>

                  {/* 最后同步卡片 */}
                  <div className="rounded-lg border bg-white p-4 dark:bg-muted/30">
                    <div className="text-muted-foreground text-xs mb-2 font-semibold">
                      {t('subscriptions.details.lastSync')}
                    </div>
                    <div className="text-sm text-foreground font-medium">
                      {(() => {
                        if (!selectedSubscription.sync_time) return t('common.neverUsed')
                        if (typeof selectedSubscription.sync_time === 'number') {
                          const timestamp = selectedSubscription.sync_time
                          const timestampLength = timestamp.toString().length
                          const adjustedTimestamp = timestampLength <= 10 ? timestamp * 1000 : timestamp
                          const date = dayjs(adjustedTimestamp)
                          if (date.isValid() && date.year() >= 1970 && date.year() < 2100) {
                            return formatTimestamp(timestamp)
                          }
                          return t('common.neverUsed')
                        }
                        return formatDateTime(selectedSubscription.sync_time)
                      })()}
                    </div>
                  </div>

                  {/* 日期范围卡片 */}
                  {selectedSubscription.min_publish_time && selectedSubscription.max_publish_time && (
                    <div className="p-4 bg-muted/30 rounded-lg border">
                      <div className="text-muted-foreground text-xs mb-2 font-semibold">
                        时间跨度
                      </div>
                      <div className="text-sm text-foreground font-medium">
                        {(() => {
                          const formatDate = (timestamp: number) => {
                            if (!timestamp) return t('common.unknownError')
                            const timestampLength = timestamp.toString().length
                            const adjustedTimestamp = timestampLength <= 10 ? timestamp * 1000 : timestamp
                            const date = dayjs(adjustedTimestamp)
                            if (date.isValid() && date.year() >= 1970 && date.year() < 2100) {
                              return date.format('YYYY-MM-DD')
                            }
                            return t('common.unknownError')
                          }
                          const startDate = formatDate(selectedSubscription.min_publish_time!)
                          const endDate = formatDate(selectedSubscription.max_publish_time!)
                          if (startDate === t('common.unknownError') || endDate === t('common.unknownError')) {
                            return t('common.noData')
                          }
                          return `${startDate} ~ ${endDate}`
                        })()}
                      </div>
                    </div>
                  )}

                  {/* 简介卡片 */}
                  <div className="col-span-full p-6 bg-muted/30 rounded-lg border">
                    <div className="text-foreground text-sm mb-3 font-semibold flex items-center gap-2">
                       {t('subscriptions.details.description')}
                    </div>
                    <div className="text-sm text-foreground/80 leading-relaxed whitespace-pre-wrap">
                      {selectedSubscription.mp_intro || t('common.noData')}
                    </div>
                  </div>

                  {/* RSS地址卡片 */}
                  {selectedSubscription.rss_url && (
                    <div className="col-span-full p-6 bg-muted/30 rounded-lg border">
                      <div className="text-foreground text-sm mb-3 font-semibold">
                        {t('subscriptions.details.rssUrl')}
                      </div>
                      <div className="text-xs font-mono bg-background p-3 rounded border break-all">
                        <a 
                          href={selectedSubscription.rss_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          {selectedSubscription.rss_url}
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card 
              className="h-full flex items-center justify-center border-dashed bg-muted/10"
            >
              <CardContent className="text-center space-y-3">
                 <div className="h-16 w-16 bg-muted rounded-full flex items-center justify-center mx-auto">
                    <Search className="h-8 w-8 text-muted-foreground/50" />
                  </div>
                <p className="text-muted-foreground text-base">
                  请从左侧列表选择一个订阅查看详情
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* 弹窗部分保持不变 */}
      <Dialog open={visible} onOpenChange={setVisible}>
        <DialogContent className="max-w-[600px]">
          <DialogHeader>
            <DialogTitle>{t('subscriptions.edit')}</DialogTitle>
            <DialogDescription>{t('subscriptions.form.editDesc')}</DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSave)} className="space-y-4">
              <FormField
                control={form.control}
                name="mp_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t('subscriptions.form.name')}</FormLabel>
                    <FormControl>
                      <Input disabled {...field} className="bg-muted" />
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
                    <FormLabel>{t('subscriptions.form.name')} <span className="text-destructive">*</span></FormLabel>
                    <FormControl>
                      <Input {...field} required />
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
                    <FormLabel>{t('subscriptions.form.description')}</FormLabel>
                    <FormControl>
                      <Textarea rows={4} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="status"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">{t('subscriptions.form.status')}</FormLabel>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setVisible(false)}>{t('common.cancel')}</Button>
                <Button type="submit">{t('common.save')}</Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('common.confirm')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('subscriptions.form.deleteConfirm')}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t('common.cancel')}</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive hover:bg-destructive/90"
              onClick={() => {
                if (deleteTargetId) {
                  handleDelete(deleteTargetId)
                  setDeleteDialogOpen(false)
                  setDeleteTargetId(null)
                }
              }}
            >
              {t('common.confirm')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export default SubscriptionManagement
