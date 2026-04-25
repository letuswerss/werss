import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { useToast } from '@/hooks/use-toast'
import { listMessageTasks, deleteMessageTask, FreshJobApi, RunMessageTask } from '@/api/messageTask'
import type { MessageTask } from '@/types/messageTask'
import {
  getNotificationEnabled,
  enableBrowserNotification,
  disableBrowserNotification,
  initBrowserNotification
} from '@/utils/browserNotification'
import { Bell, Plus, Edit, Trash2, Play, Loader2, AlertCircle, RefreshCw, FlaskConical } from 'lucide-react'

const MessageTaskList: React.FC = () => {
  const navigate = useNavigate()
  const [browserNotificationEnabled, setBrowserNotificationEnabled] = useState(false)
  const [loading, setLoading] = useState(false)
  const [taskList, setTaskList] = useState<MessageTask[]>([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null)
  const [runDialogOpen, setRunDialogOpen] = useState(false)
  const [runTargetId, setRunTargetId] = useState<number | null>(null)
  const [isTestRun, setIsTestRun] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    setBrowserNotificationEnabled(getNotificationEnabled())
    initBrowserNotification()
  }, [])

  const parseCronExpression = (exp: string) => {
    const parts = exp.split(' ')
    if (parts.length !== 5) return exp

    const [minute, hour, day, month, week] = parts
    let result = ''

    if (minute === '*') {
      result += '每分钟'
    } else if (minute.includes('/')) {
      const [, interval] = minute.split('/')
      result += `每${interval}分钟`
    } else {
      result += `在${minute}分`
    }

    if (hour === '*') {
      result += '每小时'
    } else if (hour.includes('/')) {
      const [, interval] = hour.split('/')
      result += `每${interval}小时`
    } else {
      result += ` ${hour}时`
    }

    if (day === '*') {
      result += ' 每天'
    } else if (day.includes('/')) {
      const [, interval] = day.split('/')
      result += ` 每${interval}天`
    } else {
      result += ` ${day}日`
    }

    if (month === '*') {
      result += ' 每月'
    } else if (month.includes('/')) {
      const [, interval] = month.split('/')
      result += ` 每${interval}个月`
    } else {
      result += ` ${month}月`
    }

    if (week !== '*') {
      result += ` 星期${week}`
    }

    return result || exp
  }

  const fetchTaskList = async () => {
    setLoading(true)
    try {
      const res = await listMessageTasks({
        offset: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize
      }) as any
      setTaskList(res?.list || [])
      setPagination(prev => ({ ...prev, total: res?.total || 0 }))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTaskList()
  }, [pagination.current, pagination.pageSize])

  const handleAdd = () => {
    navigate('/message-tasks/add')
  }

  const FreshJob = async () => {
    try {
      const data = await FreshJobApi()
      toast({
        title: "成功",
        description: (data as any).message || '刷新任务成功'
      })
    } catch (error) {
      toast({
        variant: "destructive",
        title: "错误",
        description: "刷新任务失败"
      })
    }
  }

  const toggleNotification = async () => {
    if (browserNotificationEnabled) {
      disableBrowserNotification()
      setBrowserNotificationEnabled(false)
      toast({
        title: "成功",
        description: "浏览器通知已关闭"
      })
    } else {
      const success = await enableBrowserNotification()
      if (success) {
        setBrowserNotificationEnabled(true)
        toast({
          title: "成功",
          description: "浏览器通知已开启，将每分钟检查新文章"
        })
      } else {
        toast({
          variant: "destructive",
          title: "错误",
          description: "开启浏览器通知失败"
        })
      }
    }
  }

  const handleEdit = (id: number) => {
    navigate(`/message-tasks/edit/${id}`)
  }

  const handleDelete = (id: number) => {
    setDeleteTargetId(id)
    setDeleteDialogOpen(true)
  }

  const confirmDelete = async () => {
    if (!deleteTargetId) return
    try {
      await deleteMessageTask(String(deleteTargetId))
      setDeleteDialogOpen(false)
      setDeleteTargetId(null)
      toast({
        title: "成功",
        description: "删除成功"
      })
      fetchTaskList()
    } catch (error) {
      toast({
        variant: "destructive",
        title: "错误",
        description: "删除失败"
      })
    }
  }

  const runTask = (id: number, isTest: boolean = false) => {
    setRunTargetId(id)
    setIsTestRun(isTest)
    setRunDialogOpen(true)
  }

  const confirmRunTask = async () => {
    if (!runTargetId) return
    try {
      const res = await RunMessageTask(String(runTargetId), isTestRun)
      setRunDialogOpen(false)
      setRunTargetId(null)
      toast({
        title: "成功",
        description: (res as any)?.message || '执行成功'
      })
    } catch (error) {
      toast({
        variant: "destructive",
        title: "错误",
        description: "执行失败"
      })
    }
  }

  const totalPages = Math.ceil(pagination.total / pagination.pageSize)

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 text-foreground">
          消息任务
        </h1>
        <p className="text-muted-foreground text-sm">管理定时消息任务</p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle>任务列表</CardTitle>
            <CardDescription>管理定时消息任务</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant={browserNotificationEnabled ? "default" : "outline"}
                    onClick={toggleNotification}
                  >
                    <Bell className="h-4 w-4 mr-2" />
                    {browserNotificationEnabled ? '通知已开启' : '开启浏览器通知'}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  {browserNotificationEnabled ? '点击关闭浏览器通知' : '开启后有新文章时浏览器标题会闪烁并播放提示音'}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" onClick={FreshJob}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    应用
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  点击应用按钮后任务才会生效
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Button 
              onClick={handleAdd}
            >
              <Plus className="h-4 w-4 mr-2" />
              添加消息任务
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Alert className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              注意：只有添加了任务消息才会定时执行更新任务，点击应用按钮后任务才会生效
            </AlertDescription>
          </Alert>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[200px]">名称</TableHead>
                  <TableHead>cron表达式</TableHead>
                  <TableHead className="w-[100px]">类型</TableHead>
                  <TableHead className="w-[100px]">状态</TableHead>
                  <TableHead className="w-[250px]">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                    </TableCell>
                  </TableRow>
                ) : taskList.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                      暂无数据
                    </TableCell>
                  </TableRow>
                ) : (
                  taskList.map((task: any) => (
                    <TableRow key={task.id}>
                      <TableCell className="font-medium truncate max-w-[200px]" title={task.name || task.message_template || ''}>
                        {task.name || task.message_template || '-'}
                      </TableCell>
                      <TableCell>{parseCronExpression(task.cron_exp || '')}</TableCell>
                      <TableCell>
                        <Badge variant={task.message_type === 1 ? "default" : "secondary"}>
                          {task.message_type === 1 ? 'WeekHook' : 'Message'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={task.status === 1 ? "default" : "outline"}>
                          {task.status === 1 ? '启用' : '禁用'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                          <Button variant="ghost" size="sm" onClick={() => handleEdit(task.id)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                              </TooltipTrigger>
                              <TooltipContent>编辑任务</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button variant="outline" size="sm" onClick={() => runTask(task.id, true)}>
                                  <FlaskConical className="h-4 w-4 mr-1.5" />
                                  <span className="text-xs">测试</span>
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>测试消息任务（仅发送消息，不更新文章）</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button variant="outline" size="sm" onClick={() => runTask(task.id, false)}>
                                  <Play className="h-4 w-4 mr-1.5" />
                                  <span className="text-xs">执行</span>
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>执行更新任务（更新文章并发送消息）</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                          <Button variant="ghost" size="sm" onClick={() => handleDelete(task.id)}>
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                              </TooltipTrigger>
                              <TooltipContent>删除任务</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                共 {pagination.total} 条，第 {pagination.current} / {totalPages} 页
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPagination(prev => ({ ...prev, current: Math.max(1, prev.current - 1) }))}
                  disabled={pagination.current === 1}
                >
                  上一页
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPagination(prev => ({ ...prev, current: Math.min(totalPages, prev.current + 1) }))}
                  disabled={pagination.current === totalPages}
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 删除确认对话框 */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>确定要删除这条消息任务吗？删除后无法恢复</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>取消</Button>
            <Button variant="destructive" onClick={confirmDelete}>确认</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 执行任务确认对话框 */}
      <Dialog open={runDialogOpen} onOpenChange={setRunDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认执行</DialogTitle>
            <DialogDescription>确定要执行这条消息任务吗？</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRunDialogOpen(false)}>取消</Button>
            <Button onClick={confirmRunTask}>确认</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default MessageTaskList
