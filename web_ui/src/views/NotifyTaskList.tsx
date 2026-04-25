import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { useToast } from '@/hooks/use-toast'
import { listNotifyTasks, deleteNotifyTask, reloadNotifyJobs, runNotifyTask } from '@/api/notifyTask'
import type { NotifyTask } from '@/types/notifyTask'
import { AlertCircle, Edit, Loader2, Play, Plus, RefreshCw, Trash2 } from 'lucide-react'

const NotifyTaskListView: React.FC = () => {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [list, setList] = useState<NotifyTask[]>([])
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null)
  const [runDialogOpen, setRunDialogOpen] = useState(false)
  const [runTargetId, setRunTargetId] = useState<string | null>(null)

  const fetchList = async () => {
    setLoading(true)
    try {
      const res = await listNotifyTasks({
        offset: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
      }) as any
      setList(res?.list || [])
      setPagination(prev => ({ ...prev, total: res?.total || 0 }))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchList() }, [pagination.current, pagination.pageSize])

  const handleAdd = () => navigate('/notify-tasks/add')
  const handleEdit = (id: string) => navigate(`/notify-tasks/edit/${id}`)

  const handleReload = async () => {
    try {
      const res = await reloadNotifyJobs()
      toast({ title: '成功', description: (res as any)?.message || '推送任务已重载' })
    } catch {
      toast({ variant: 'destructive', title: '错误', description: '重载失败' })
    }
  }

  const askDelete = (id: string) => { setDeleteTargetId(id); setDeleteDialogOpen(true) }
  const confirmDelete = async () => {
    if (!deleteTargetId) return
    try {
      await deleteNotifyTask(deleteTargetId)
      setDeleteDialogOpen(false)
      setDeleteTargetId(null)
      toast({ title: '成功', description: '删除成功' })
      fetchList()
    } catch {
      toast({ variant: 'destructive', title: '错误', description: '删除失败' })
    }
  }

  const askRun = (id: string) => { setRunTargetId(id); setRunDialogOpen(true) }
  const confirmRun = async () => {
    if (!runTargetId) return
    try {
      const res = await runNotifyTask(runTargetId)
      setRunDialogOpen(false)
      setRunTargetId(null)
      toast({ title: '成功', description: (res as any)?.message || '已加入队列' })
    } catch {
      toast({ variant: 'destructive', title: '错误', description: '执行失败' })
    }
  }

  const totalPages = Math.ceil(pagination.total / pagination.pageSize)

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 text-foreground">推送任务</h1>
        <p className="text-muted-foreground text-sm">按 cron 把数据库里的文章渲染并推到 webhook，不做任何抓取</p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle>任务列表</CardTitle>
            <CardDescription>仅负责推送；文章采集请前往「抓取任务」配置</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" onClick={handleReload}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    应用
                  </Button>
                </TooltipTrigger>
                <TooltipContent>修改后点击应用，调度器才会按新配置生效</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Button onClick={handleAdd}>
              <Plus className="h-4 w-4 mr-2" />
              添加推送任务
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Alert className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              推送任务只读取数据库已有文章，不会去抓取。请先在「抓取任务」里把文章拉进来。
            </AlertDescription>
          </Alert>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[200px]">名称</TableHead>
                  <TableHead>cron 表达式</TableHead>
                  <TableHead className="w-[100px]">类型</TableHead>
                  <TableHead className="w-[100px]">状态</TableHead>
                  <TableHead className="w-[220px]">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                    </TableCell>
                  </TableRow>
                ) : list.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">暂无数据</TableCell>
                  </TableRow>
                ) : (
                  list.map((task) => (
                    <TableRow key={task.id}>
                      <TableCell className="font-medium truncate max-w-[200px]" title={task.name}>{task.name || '-'}</TableCell>
                      <TableCell><code className="text-xs">{task.cron_exp}</code></TableCell>
                      <TableCell>
                        <Badge variant={task.message_type === 1 ? 'default' : 'secondary'}>
                          {task.message_type === 1 ? 'WebHook' : 'Message'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={task.status === 1 ? 'default' : 'outline'}>
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
                                <Button variant="outline" size="sm" onClick={() => askRun(task.id)}>
                                  <Play className="h-4 w-4 mr-1.5" />
                                  <span className="text-xs">执行</span>
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>立即触发一次推送</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button variant="ghost" size="sm" onClick={() => askDelete(task.id)}>
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
                <Button variant="outline" size="sm" onClick={() => setPagination(prev => ({ ...prev, current: Math.max(1, prev.current - 1) }))} disabled={pagination.current === 1}>上一页</Button>
                <Button variant="outline" size="sm" onClick={() => setPagination(prev => ({ ...prev, current: Math.min(totalPages, prev.current + 1) }))} disabled={pagination.current === totalPages}>下一页</Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>确定要删除这条推送任务吗？删除后无法恢复</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>取消</Button>
            <Button variant="destructive" onClick={confirmDelete}>确认</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={runDialogOpen} onOpenChange={setRunDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认执行</DialogTitle>
            <DialogDescription>立即触发一次推送，会读取当天的文章并推到 webhook</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRunDialogOpen(false)}>取消</Button>
            <Button onClick={confirmRun}>确认</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default NotifyTaskListView
