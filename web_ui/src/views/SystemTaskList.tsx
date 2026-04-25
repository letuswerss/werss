import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useToast } from '@/hooks/use-toast'
import {
  getSystemTasks,
  reloadSystemTasks,
  runArticleRetention,
  updateArticleRetention,
  updateHotTopicsSchedule,
  deleteHotTopicsSchedule,
  runHotTopicsNow,
  type ArticleRetentionConfig,
  type HotTopicsScheduleConfig,
  type SystemTaskItem,
} from '@/api/systemTask'
import {
  type CronPresetId,
  cronFromPreset,
  detectCronPreset,
} from '@/lib/hotTopicsSchedule'
import { AlertTriangle, ArrowRight, Flame, Loader2, Play, RefreshCw, Save, Trash2 } from 'lucide-react'

const emptyRetention: ArticleRetentionConfig = {
  enabled: false,
  cron: '0 4 * * *',
  days: 7,
  basis: 'created_at',
  next_run: null,
}

const emptyHotTopics: HotTopicsScheduleConfig = {
  enabled: true,
  cron: '0 9 * * *',
  window_days: 3,
  max_topics: 5,
  next_run: null,
}

const formatNextRun = (value?: string | null) => {
  if (!value) return '未注册'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
}

const SystemTaskList: React.FC = () => {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [reloading, setReloading] = useState(false)
  const [running, setRunning] = useState(false)
  const [tasks, setTasks] = useState<SystemTaskItem[]>([])
  const [retention, setRetention] = useState<ArticleRetentionConfig>(emptyRetention)
  const [draft, setDraft] = useState<ArticleRetentionConfig>(emptyRetention)
  const [hotSaved, setHotSaved] = useState<HotTopicsScheduleConfig>(emptyHotTopics)
  const [hotDraft, setHotDraft] = useState<HotTopicsScheduleConfig>(emptyHotTopics)
  const [hotPreset, setHotPreset] = useState<CronPresetId>('daily')
  const [hotDailyHour, setHotDailyHour] = useState(9)
  const [savingHot, setSavingHot] = useState(false)
  const [runningHot, setRunningHot] = useState(false)
  const [deleteHotOpen, setDeleteHotOpen] = useState(false)
  const [runDialogOpen, setRunDialogOpen] = useState(false)

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await getSystemTasks()
      setTasks(res.tasks || [])
      const nextHot = res.hot_topics || emptyHotTopics
      setHotSaved(nextHot)
      setHotDraft(nextHot)
      const hp = detectCronPreset(nextHot.cron)
      setHotPreset(hp.preset)
      setHotDailyHour(hp.dailyHour)
      const nextRetention = res.article_retention || emptyRetention
      setRetention(nextRetention)
      setDraft(nextRetention)
    } catch {
      toast({ variant: 'destructive', title: '加载失败', description: '无法获取系统定时任务' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadData()
  }, [])

  const changed = useMemo(() => (
    draft.enabled !== retention.enabled ||
    draft.cron !== retention.cron ||
    draft.days !== retention.days ||
    draft.basis !== retention.basis
  ), [draft, retention])

  const hotChanged = useMemo(() => (
    hotDraft.enabled !== hotSaved.enabled ||
    hotDraft.cron !== hotSaved.cron ||
    hotDraft.window_days !== hotSaved.window_days ||
    hotDraft.max_topics !== hotSaved.max_topics
  ), [hotDraft, hotSaved])

  const saveRetention = async () => {
    if (!draft.cron.trim()) {
      toast({ variant: 'destructive', title: '保存失败', description: 'cron 表达式不能为空' })
      return
    }
    if (draft.days < 1) {
      toast({ variant: 'destructive', title: '保存失败', description: '保留天数至少为 1' })
      return
    }
    setSaving(true)
    try {
      const res = await updateArticleRetention({
        enabled: draft.enabled,
        cron: draft.cron.trim(),
        days: Math.min(9999, Math.max(1, Math.floor(draft.days))),
        basis: draft.basis,
      })
      setTasks(res.tasks || [])
      if (res.hot_topics) {
        setHotSaved(res.hot_topics)
        setHotDraft(res.hot_topics)
        const hp = detectCronPreset(res.hot_topics.cron)
        setHotPreset(hp.preset)
        setHotDailyHour(hp.dailyHour)
      }
      const nextRetention = res.article_retention || draft
      setRetention(nextRetention)
      setDraft(nextRetention)
      toast({ title: '已保存', description: '文章定期清理任务已重载生效' })
    } catch {
      toast({ variant: 'destructive', title: '保存失败', description: '请检查 cron 表达式或稍后重试' })
    } finally {
      setSaving(false)
    }
  }

  const reloadAll = async () => {
    setReloading(true)
    try {
      const res = await reloadSystemTasks()
      setTasks(res.tasks || [])
      if (res.hot_topics) {
        setHotSaved(res.hot_topics)
        setHotDraft(res.hot_topics)
        const hp = detectCronPreset(res.hot_topics.cron)
        setHotPreset(hp.preset)
        setHotDailyHour(hp.dailyHour)
      }
      const nextRetention = res.article_retention || retention
      setRetention(nextRetention)
      setDraft(nextRetention)
      toast({ title: '已重载', description: '全部定时任务已按最新配置重新注册' })
    } catch {
      toast({ variant: 'destructive', title: '重载失败', description: '请稍后重试' })
    } finally {
      setReloading(false)
    }
  }

  const saveHotTopics = async () => {
    if (!hotDraft.cron.trim()) {
      toast({ variant: 'destructive', title: '保存失败', description: 'cron 表达式不能为空' })
      return
    }
    setSavingHot(true)
    try {
      const res = await updateHotTopicsSchedule({
        enabled: hotDraft.enabled,
        cron: hotDraft.cron.trim(),
        window_days: Math.min(30, Math.max(1, Math.floor(hotDraft.window_days))),
        max_topics: Math.min(20, Math.max(3, Math.floor(hotDraft.max_topics))),
      })
      setTasks(res.tasks || [])
      if (res.hot_topics) {
        setHotSaved(res.hot_topics)
        setHotDraft(res.hot_topics)
        const hp = detectCronPreset(res.hot_topics.cron)
        setHotPreset(hp.preset)
        setHotDailyHour(hp.dailyHour)
      }
      toast({ title: '已保存', description: '热点发现定时任务已重载生效' })
    } catch {
      toast({ variant: 'destructive', title: '保存失败', description: '请检查配置或稍后重试' })
    } finally {
      setSavingHot(false)
    }
  }

  const confirmDeleteHotSchedule = async () => {
    setSavingHot(true)
    try {
      const res = await deleteHotTopicsSchedule()
      setDeleteHotOpen(false)
      setTasks(res.tasks || [])
      if (res.hot_topics) {
        setHotSaved(res.hot_topics)
        setHotDraft(res.hot_topics)
        const hp = detectCronPreset(res.hot_topics.cron)
        setHotPreset(hp.preset)
        setHotDailyHour(hp.dailyHour)
      }
      toast({ title: '已关闭', description: '热点发现定时任务已停用' })
    } catch {
      toast({ variant: 'destructive', title: '操作失败', description: '请稍后重试' })
    } finally {
      setSavingHot(false)
    }
  }

  const runHotOnce = async () => {
    setRunningHot(true)
    try {
      const res = await runHotTopicsNow() as { topic_count?: number; run_id?: string }
      toast({
        title: '热点发现完成',
        description: `发现 ${res?.topic_count ?? 0} 个主题`,
      })
      void loadData()
    } catch {
      toast({ variant: 'destructive', title: '执行失败', description: '请确认已配置 LLM 且网络可用' })
    } finally {
      setRunningHot(false)
    }
  }

  const confirmRunRetention = async () => {
    setRunning(true)
    try {
      const res = await runArticleRetention() as any
      setRunDialogOpen(false)
      toast({
        title: '清理完成',
        description: `处理 ${res?.total ?? 0} 篇文章，${res?.batches ?? 0} 个批次`,
      })
      void loadData()
    } catch {
      toast({ variant: 'destructive', title: '执行失败', description: '文章清理执行失败' })
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-foreground">定时任务</h1>
          <p className="text-sm text-muted-foreground">
            统一查看系统内所有 cron 任务：抓取、推送、热点发现、文章定期清理。
          </p>
        </div>
        <Button variant="outline" onClick={reloadAll} disabled={reloading}>
          {reloading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
          重载全部任务
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>任务总览</CardTitle>
          <CardDescription>
            抓取/推送是多任务表；热点发现和文章清理是配置驱动的系统任务。
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[180px]">任务</TableHead>
                  <TableHead className="w-[100px]">状态</TableHead>
                  <TableHead>说明</TableHead>
                  <TableHead className="w-[180px]">cron</TableHead>
                  <TableHead className="w-[220px]">下次执行</TableHead>
                  <TableHead className="w-[120px]">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                    </TableCell>
                  </TableRow>
                ) : tasks.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">暂无任务</TableCell>
                  </TableRow>
                ) : (
                  tasks.map((task) => (
                    <TableRow key={task.key}>
                      <TableCell className="font-medium">{task.name}</TableCell>
                      <TableCell>
                        <Badge variant={task.enabled ? 'default' : 'outline'}>
                          {task.enabled ? '启用' : '禁用'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">{task.summary}</TableCell>
                      <TableCell>
                        <code className="text-xs">{task.cron}</code>
                      </TableCell>
                      <TableCell className="text-sm">{formatNextRun(task.next_run)}</TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" onClick={() => navigate(task.manage_path)}>
                          管理
                          <ArrowRight className="h-4 w-4 ml-1" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Card id="hot-topics">
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1.5">
              <CardTitle className="flex items-center gap-2">
                <Flame className="h-5 w-5" />
                热点发现（定时）
              </CardTitle>
              <CardDescription>
                使用 cron 安排自动分析；时间窗口与主题数与「热点发现」页手动分析一致，保存后写入配置库并重载调度器。
              </CardDescription>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Button variant="outline" size="sm" onClick={() => void runHotOnce()} disabled={runningHot || loading}>
                {runningHot ? <Loader2 className="h-4 w-4 mr-1.5 animate-spin" /> : <Play className="h-4 w-4 mr-1.5" />}
                立即执行
              </Button>
              <Switch
                checked={hotDraft.enabled}
                disabled={loading || savingHot}
                onCheckedChange={(checked) => setHotDraft(prev => ({ ...prev, enabled: checked }))}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2 lg:col-span-2">
              <Label>执行计划</Label>
              <Select
                value={hotPreset}
                disabled={loading || savingHot}
                onValueChange={(v) => {
                  const p = v as CronPresetId
                  setHotPreset(p)
                  if (p === 'custom') return
                  const nc = cronFromPreset(p, hotDailyHour)
                  setHotDraft(prev => ({ ...prev, cron: nc }))
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="every_1h">每 1 小时</SelectItem>
                  <SelectItem value="every_2h">每 2 小时</SelectItem>
                  <SelectItem value="every_3h">每 3 小时</SelectItem>
                  <SelectItem value="every_6h">每 6 小时</SelectItem>
                  <SelectItem value="every_12h">每 12 小时</SelectItem>
                  <SelectItem value="daily">每天一次（选时刻）</SelectItem>
                  <SelectItem value="custom">自定义 cron</SelectItem>
                </SelectContent>
              </Select>
              {hotPreset === 'daily' && (
                <div className="flex items-center gap-2 pt-1">
                  <Label className="text-xs text-muted-foreground whitespace-nowrap">每天</Label>
                  <Input
                    type="number"
                    min={0}
                    max={23}
                    className="w-[88px]"
                    value={hotDailyHour}
                    disabled={loading || savingHot}
                    onChange={(e) => {
                      const n = Math.min(23, Math.max(0, parseInt(e.target.value, 10) || 0))
                      setHotDailyHour(n)
                      setHotDraft(prev => ({ ...prev, cron: cronFromPreset('daily', n) }))
                    }}
                  />
                  <span className="text-xs text-muted-foreground">点整（0–23）</span>
                </div>
              )}
            </div>
            <div className="space-y-2 lg:col-span-2">
              <Label htmlFor="hot-cron">cron 表达式</Label>
              <Input
                id="hot-cron"
                value={hotDraft.cron}
                disabled={loading || savingHot}
                onChange={(e) => {
                  const v = e.target.value
                  setHotDraft(prev => ({ ...prev, cron: v }))
                  const d = detectCronPreset(v)
                  setHotPreset(d.preset)
                  if (d.preset === 'daily') setHotDailyHour(d.dailyHour)
                }}
                placeholder="0 9 * * *"
              />
              <p className="text-xs text-muted-foreground">五段：分 时 日 月 周。改这里会识别为「自定义」或匹配快捷项。</p>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="hot-window">分析时间窗口（天）</Label>
              <Input
                id="hot-window"
                type="number"
                min={1}
                max={30}
                value={hotDraft.window_days}
                disabled={loading || savingHot}
                onChange={(e) => {
                  const n = Math.min(30, Math.max(1, parseInt(e.target.value, 10) || 1))
                  setHotDraft(prev => ({ ...prev, window_days: n }))
                }}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="hot-max">最大热点数</Label>
              <Input
                id="hot-max"
                type="number"
                min={3}
                max={20}
                value={hotDraft.max_topics}
                disabled={loading || savingHot}
                onChange={(e) => {
                  const n = Math.min(20, Math.max(3, parseInt(e.target.value, 10) || 3))
                  setHotDraft(prev => ({ ...prev, max_topics: n }))
                }}
              />
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-sm text-muted-foreground">
              下次执行：{formatNextRun(hotSaved.next_run)}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="destructive"
                onClick={() => setDeleteHotOpen(true)}
                disabled={savingHot || !hotSaved.enabled}
              >
                删除定时任务
              </Button>
              <Button
                onClick={saveHotTopics}
                disabled={savingHot || !hotChanged || !hotDraft.cron.trim()}
              >
                {savingHot ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                保存并应用
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card id="article-retention">
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1.5">
              <CardTitle className="flex items-center gap-2">
                <Trash2 className="h-5 w-5" />
                文章定期清理任务
              </CardTitle>
              <CardDescription>
                按保留天数清理旧文章及关联标签、AI 筛选记录。这里保存后会自动重载调度器。
              </CardDescription>
            </div>
            <Switch
              checked={draft.enabled}
              disabled={loading || saving}
              onCheckedChange={(checked) => setDraft(prev => ({ ...prev, enabled: checked }))}
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              立即执行会按当前保留策略删除或标记旧文章；实际物理删除/逻辑删除遵循
              <code className="mx-1 text-[0.75rem]">article.true_delete</code> 配置。
            </AlertDescription>
          </Alert>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="retention-cron">cron 表达式</Label>
              <Input
                id="retention-cron"
                value={draft.cron}
                disabled={loading || saving}
                onChange={(event) => setDraft(prev => ({ ...prev, cron: event.target.value }))}
                placeholder="0 4 * * *"
              />
              <p className="text-xs text-muted-foreground">默认每天 04:00 执行</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="retention-days">保留最近</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="retention-days"
                  type="number"
                  min={1}
                  max={9999}
                  value={draft.days}
                  disabled={loading || saving}
                  onChange={(event) => {
                    const value = parseInt(event.target.value, 10)
                    setDraft(prev => ({ ...prev, days: Number.isNaN(value) ? 1 : value }))
                  }}
                />
                <span className="text-sm text-muted-foreground whitespace-nowrap">天</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label>时间基准</Label>
              <Select
                value={draft.basis}
                disabled={loading || saving}
                onValueChange={(value) => setDraft(prev => ({ ...prev, basis: value as ArticleRetentionConfig['basis'] }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="created_at">入库时间 created_at</SelectItem>
                  <SelectItem value="publish_time">微信发布时间 publish_time</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-sm text-muted-foreground">
              下次执行：{formatNextRun(retention.next_run)}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="outline" onClick={() => setRunDialogOpen(true)} disabled={running}>
                <Play className="h-4 w-4 mr-2" />
                立即执行一次
              </Button>
              <Button onClick={saveRetention} disabled={saving || !changed || draft.days < 1 || !draft.cron.trim()}>
                {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                保存并应用
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={deleteHotOpen} onOpenChange={setDeleteHotOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>关闭热点发现定时任务？</DialogTitle>
            <DialogDescription>
              将停用自动调度，不会删除已有热点数据。需要时可再次打开开关并保存。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteHotOpen(false)} disabled={savingHot}>
              取消
            </Button>
            <Button variant="destructive" onClick={() => void confirmDeleteHotSchedule()} disabled={savingHot}>
              {savingHot ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
              确认关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={runDialogOpen} onOpenChange={setRunDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认立即执行文章清理？</DialogTitle>
            <DialogDescription>
              系统会按照当前已保存的保留策略清理过期文章。请确认保留天数和删除方式符合预期。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRunDialogOpen(false)} disabled={running}>取消</Button>
            <Button variant="destructive" onClick={confirmRunRetention} disabled={running}>
              {running && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              确认执行
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default SystemTaskList
