import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useToast } from '@/hooks/use-toast'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { getRecentHotTopics, rebuildHotTopics } from '@/api/hotTopics'
import { getSystemTasks, updateHotTopicsSchedule } from '@/api/systemTask'
import {
  type CronPresetId,
  cronFromPreset,
  detectCronPreset,
} from '@/lib/hotTopicsSchedule'
import type { HotTopicsResponse } from '@/types/hotTopic'
import {
  Flame,
  Loader2,
  RefreshCw,
  TrendingUp,
  Calendar,
  FileText,
  ChevronDown,
  ChevronUp,
  Settings
} from 'lucide-react'

const HotTopics: React.FC = () => {
  const { t } = useTranslation()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [rebuilding, setRebuilding] = useState(false)
  const [rebuildStartedAt, setRebuildStartedAt] = useState<number | null>(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [data, setData] = useState<HotTopicsResponse | null>(null)
  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(new Set())
  const [showSettings, setShowSettings] = useState(false)
  const [windowDays, setWindowDays] = useState(3)
  const [maxTopics, setMaxTopics] = useState(5)
  const [scheduleEnabled, setScheduleEnabled] = useState(true)
  const [hotCron, setHotCron] = useState('0 9 * * *')
  const [hotPreset, setHotPreset] = useState<CronPresetId>('daily')
  const [hotDailyHour, setHotDailyHour] = useState(9)
  const [scheduleLoading, setScheduleLoading] = useState(false)
  const [scheduleSaving, setScheduleSaving] = useState(false)

  useEffect(() => {
    if (!rebuilding || rebuildStartedAt === null) {
      setElapsedSeconds(0)
      return
    }

    setElapsedSeconds(Math.floor((Date.now() - rebuildStartedAt) / 1000))
    const timer = window.setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - rebuildStartedAt) / 1000))
    }, 1000)

    return () => window.clearInterval(timer)
  }, [rebuilding, rebuildStartedAt])

  const loadHotTopics = async () => {
    setLoading(true)
    try {
      const res = (await getRecentHotTopics()) as unknown as HotTopicsResponse
      setData(res)
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: t('common.error'),
        description: error?.response?.data?.message || error?.message || t('hotTopics.loadError'),
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHotTopics()
  }, [])

  useEffect(() => {
    if (!showSettings) return
    let cancelled = false
    setScheduleLoading(true)
    void (async () => {
      try {
        const res = await getSystemTasks()
        if (cancelled || !res?.hot_topics) return
        const ht = res.hot_topics
        setWindowDays(ht.window_days)
        setMaxTopics(ht.max_topics)
        setScheduleEnabled(ht.enabled)
        setHotCron(ht.cron)
        const hp = detectCronPreset(ht.cron)
        setHotPreset(hp.preset)
        setHotDailyHour(hp.dailyHour)
      } catch {
        // 未登录或无权限时忽略，仍可用当前本地默认值手动分析
      } finally {
        if (!cancelled) setScheduleLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [showSettings])

  const saveSchedule = async () => {
    if (!hotCron.trim()) {
      toast({ variant: 'destructive', title: '保存失败', description: '请填写有效的 cron 表达式' })
      return
    }
    setScheduleSaving(true)
    try {
      await updateHotTopicsSchedule({
        enabled: scheduleEnabled,
        cron: hotCron.trim(),
        window_days: Math.min(30, Math.max(1, Math.floor(windowDays))),
        max_topics: Math.min(20, Math.max(3, Math.floor(maxTopics))),
      })
      toast({ title: '已保存', description: '热点发现定时任务已按当前配置重载' })
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: t('common.error'),
        description: error?.message || '保存失败',
      })
    } finally {
      setScheduleSaving(false)
    }
  }

  const rebuild = async () => {
    setRebuilding(true)
    setRebuildStartedAt(Date.now())
    setShowSettings(false)
    try {
      const res = await rebuildHotTopics({ window_days: windowDays, max_topics: maxTopics }) as any
      const n = res?.data?.topic_count ?? 0
      toast({
        title: t('hotTopics.toastSuccess'),
        description: res?.data?.message || t('hotTopics.toastSuccessWithCount', { count: n }),
      })
      await loadHotTopics()
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: t('hotTopics.toastFail'),
        description: error?.response?.data?.message || error?.message || t('hotTopics.toastFailRetry'),
      })
    } finally {
      setRebuilding(false)
      setRebuildStartedAt(null)
    }
  }

  const toggleExpand = (topicId: string) => {
    setExpandedTopics(prev => {
      const next = new Set(prev)
      if (next.has(topicId)) {
        next.delete(topicId)
      } else {
        next.add(topicId)
      }
      return next
    })
  }

  const elapsedMinutes = Math.floor(elapsedSeconds / 60)
  const elapsedRemainingSeconds = elapsedSeconds % 60
  const elapsedText = `${String(elapsedMinutes).padStart(2, '0')}:${String(elapsedRemainingSeconds).padStart(2, '0')}`

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="p-6 space-y-6">
      <Dialog open={rebuilding}>
        <DialogContent
          className="sm:max-w-[520px] [&>button]:hidden"
          onEscapeKeyDown={(event) => event.preventDefault()}
          onPointerDownOutside={(event) => event.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin" />
              {t('hotTopics.dialogTitle')}
            </DialogTitle>
            <DialogDescription className="pt-1">
              {t('hotTopics.dialogDescription')}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="rounded-lg border bg-muted/30 p-4">
              <div className="flex items-center justify-between gap-4">
                <span className="text-sm font-medium">{t('hotTopics.elapsed')}</span>
                <span className="font-mono text-lg font-semibold">{elapsedText}</span>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-muted">
                <div className="h-full w-1/3 animate-pulse rounded-full bg-primary" />
              </div>
            </div>

            <div className="space-y-2 text-sm text-muted-foreground">
              <p>{t('hotTopics.dialogHint1')}</p>
              <p>{t('hotTopics.dialogHint2')}</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 设置对话框 */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent className="sm:max-w-[520px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>热点发现设置</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            时间窗口与主题数会同时用于「立即分析 / 自动定时」；定时规则也可在
            <Link
              to="/system-tasks#hot-topics"
              className="text-primary mx-1 hover:underline"
              onClick={() => setShowSettings(false)}
            >
              定时任务
            </Link>
            中配置。
          </p>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="window-days">时间窗口（天数）</Label>
              <Input
                id="window-days"
                type="number"
                min="1"
                max="30"
                value={windowDays}
                disabled={scheduleLoading}
                onChange={(e) => setWindowDays(Math.min(30, Math.max(1, Number(e.target.value))))}
              />
              <p className="text-xs text-muted-foreground">分析最近几天内的文章，范围 1-30 天</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="max-topics">最大热点数量</Label>
              <Input
                id="max-topics"
                type="number"
                min="3"
                max="20"
                value={maxTopics}
                disabled={scheduleLoading}
                onChange={(e) => setMaxTopics(Math.min(20, Math.max(3, Number(e.target.value))))}
              />
              <p className="text-xs text-muted-foreground">返回的热点数量，范围 3-20</p>
            </div>

            <Separator />

            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium">定时自动发现</p>
                <p className="text-xs text-muted-foreground">按下方计划调用 AI；关闭后仅保留手动分析</p>
              </div>
              <Switch
                checked={scheduleEnabled}
                disabled={scheduleLoading}
                onCheckedChange={setScheduleEnabled}
              />
            </div>

            <div className="space-y-2">
              <Label>执行计划</Label>
              <Select
                value={hotPreset}
                disabled={scheduleLoading}
                onValueChange={(v) => {
                  const p = v as CronPresetId
                  setHotPreset(p)
                  if (p === 'custom') return
                  setHotCron(cronFromPreset(p, hotDailyHour))
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
                  <SelectItem value="daily">每天一次</SelectItem>
                  <SelectItem value="custom">自定义 cron</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {hotPreset === 'daily' && (
              <div className="flex items-center gap-2">
                <Label className="text-xs text-muted-foreground whitespace-nowrap">每天</Label>
                <Input
                  type="number"
                  min={0}
                  max={23}
                  className="w-[88px]"
                  value={hotDailyHour}
                  disabled={scheduleLoading}
                  onChange={(e) => {
                    const n = Math.min(23, Math.max(0, parseInt(e.target.value, 10) || 0))
                    setHotDailyHour(n)
                    setHotCron(cronFromPreset('daily', n))
                  }}
                />
                <span className="text-xs text-muted-foreground">点整</span>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="hot-cron-inline">cron（分 时 日 月 周）</Label>
              <Input
                id="hot-cron-inline"
                value={hotCron}
                disabled={scheduleLoading}
                onChange={(e) => {
                  const v = e.target.value
                  setHotCron(v)
                  const d = detectCronPreset(v)
                  setHotPreset(d.preset)
                  if (d.preset === 'daily') setHotDailyHour(d.dailyHour)
                }}
                placeholder="0 9 * * *"
              />
            </div>

            <Button
              type="button"
              className="w-full"
              variant="secondary"
              disabled={scheduleLoading || scheduleSaving}
              onClick={saveSchedule}
            >
              {scheduleSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              保存定时配置
            </Button>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setShowSettings(false)}>
              关闭
            </Button>
            <Button onClick={rebuild} disabled={rebuilding}>
              开始分析
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold">{t('hotTopics.pageTitle')}</h1>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">
            {t('hotTopics.pageSubtitle')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={() => setShowSettings(true)} title="设置">
            <Settings className="h-4 w-4" />
          </Button>
          <Button variant="outline" onClick={loadHotTopics} disabled={loading || rebuilding}>
            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
            {t('hotTopics.refresh')}
          </Button>
          <Button onClick={rebuild} disabled={loading || rebuilding}>
            {rebuilding ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <TrendingUp className="mr-2 h-4 w-4" />}
            {t('hotTopics.rebuild')}
          </Button>
        </div>
      </div>

      {data && data.run_id && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              {t('hotTopics.runInfo')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">{t('hotTopics.analyzedAt')}</span>
                <p className="font-medium">{formatDate(data.created_at)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">{t('hotTopics.window')}</span>
                <p className="font-medium">{t('hotTopics.windowDays', { days: data.window_days })}</p>
              </div>
              <div>
                <span className="text-muted-foreground">{t('hotTopics.topicCount')}</span>
                <p className="font-medium">{data.topics.length}</p>
              </div>
              <div>
                <span className="text-muted-foreground">{t('hotTopics.model')}</span>
                <p className="font-medium">{data.model_name || '-'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {data && data.topics.length === 0 && !loading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Flame className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">{t('hotTopics.empty')}</p>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {data?.topics.map((topic, index) => (
          <Card key={topic.id} className="overflow-hidden">
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1">
                  <div className="flex items-center justify-center h-8 w-8 rounded-full bg-orange-100 text-orange-600 font-bold text-sm">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-xl">{topic.topic_name}</CardTitle>
                    <CardDescription className="mt-1">{topic.summary}</CardDescription>
                  </div>
                </div>
                <Badge variant="secondary" className="shrink-0">
                  <FileText className="mr-1 h-3 w-3" />
                  {t('hotTopics.articlesCount', { count: topic.article_count })}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topic.signals && topic.signals.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {topic.signals.map((signal, idx) => (
                      <Badge key={idx} variant="outline">
                        {signal}
                      </Badge>
                    ))}
                  </div>
                )}

                <Separator />

                <div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-between"
                    onClick={() => toggleExpand(topic.id)}
                  >
                    <span className="text-sm">{t('hotTopics.relatedArticles')}</span>
                    {expandedTopics.has(topic.id) ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                  </Button>

                  {expandedTopics.has(topic.id) && (
                    <div className="mt-3 space-y-2">
                      {topic.representative_titles && topic.representative_titles.length > 0 ? (
                        topic.representative_titles.map((title, idx) => (
                          <div key={idx} className="text-sm text-muted-foreground truncate px-2">
                            • {title}
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-muted-foreground px-2">{t('hotTopics.noTitles')}</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default HotTopics
