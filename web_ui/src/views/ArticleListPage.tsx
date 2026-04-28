import React, { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle } from '@/components/ui/drawer'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Checkbox } from '@/components/ui/checkbox'
import { Switch } from '@/components/ui/switch'
import { useToast } from '@/hooks/use-toast'
import {
  getArticles,
  deleteArticle as deleteArticleApi,
  ArticleListResult,
  Article,
  getArticleDetail,
  updateArticle,
  UpdateArticleParams,
  analyzeArticleAiFilter,
  restoreArticleAiFilter,
  getUnfilteredArticleIds,
  getAllArticleIdsForAiFilter,
  ArticleAiFilterAnalyzeResult,
} from '@/api/article'
import { getSubscriptions, SubscriptionListResult } from '@/api/subscription'
import { formatDateTime } from '@/utils/date'
import dayjs from 'dayjs'
import ExportModal from '@/components/ExportModal'
import { Trash2, Download, Wifi, ChevronDown, Loader2, Edit, Tags, Search, RotateCcw, Sparkles, Undo2, EyeOff, Info, CheckCircle2, Ban } from 'lucide-react'
import { reExtractTags, startMissingTagsJob, getMissingTagsJobStatus } from '@/api/tools'

const AI_FILTER_BATCH_SIZE = 1
const AI_FILTER_TASK_STORAGE_KEY = 'werss:article-ai-filter-task'

type AiFilterTaskStatus = 'idle' | 'running' | 'paused' | 'stopped' | 'completed' | 'error'

interface AiFilterTaskState {
  total: number
  processed: number
  hidden: number
  keep: number
  maybe: number
  pendingIds: string[]
  currentBatchIds: string[]
  status: AiFilterTaskStatus
  source: 'selection' | 'page' | 'saved' | 'full'
  errorMessage?: string
}

const ArticleListPage: React.FC = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [articles, setArticles] = useState<Article[]>([])
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })
  const [searchText, setSearchText] = useState('')
  const [mpId, setMpId] = useState<string>('')
  const [mpList, setMpList] = useState<Array<{ mp_id: string; mp_name: string }>>([])
  const [articleModalVisible, setArticleModalVisible] = useState(false)
  const [currentArticle, setCurrentArticle] = useState<Article | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState<string | number | null>(null)
  const [batchDeleteDialogOpen, setBatchDeleteDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editingArticle, setEditingArticle] = useState<Article | null>(null)
  const [editFormData, setEditFormData] = useState<UpdateArticleParams>({
    title: '',
    description: '',
    url: '',
    pic_url: ''
  })
  /** 标签提取确认：selected=选中 | page=当前页 | all=全库重提 | missing=仅无标签补充 */
  const [tagExtractOpen, setTagExtractOpen] = useState(false)
  const [tagExtractKind, setTagExtractKind] = useState<'selected' | 'page' | 'all' | 'missing' | null>(null)
  const [tagExtracting, setTagExtracting] = useState(false)
  /** 补充缺失标签：异步任务进度（轮询 status） */
  const [missingTagJob, setMissingTagJob] = useState<{
    job_id: string
    total: number
    processed: number
    success_count?: number
    error_count?: number
    status: string
    message?: string
    elapsed_seconds?: number | null
  } | null>(null)
  const missingPollAbortRef = useRef(false)
  const [aiFiltering, setAiFiltering] = useState(false)
  /** 全库重新过滤：确认弹窗（与标签提取二次确认一致） */
  const [aiFilterAllConfirmOpen, setAiFilterAllConfirmOpen] = useState(false)
  const [aiFilterDialogOpen, setAiFilterDialogOpen] = useState(false)
  const [aiFilterTask, setAiFilterTask] = useState<AiFilterTaskState | null>(null)
  const [hideAiFiltered, setHideAiFiltered] = useState(true)
  const [jumpPageInput, setJumpPageInput] = useState('1')
  const [statusUpdatingIds, setStatusUpdatingIds] = useState<string[]>([])
  const [articleDetailLoading, setArticleDetailLoading] = useState(false)
  const exportModalRef = React.useRef<any>(null)
  const aiFilterControlRef = useRef<'running' | 'paused' | 'stopped'>('running')
  const articleModalVisibleRef = useRef(articleModalVisible)
  const currentArticleRef = useRef<Article | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    articleModalVisibleRef.current = articleModalVisible
    currentArticleRef.current = currentArticle
  }, [articleModalVisible, currentArticle])

  const loadMpList = async () => {
    try {
      const res = await getSubscriptions({ page: 0, pageSize: 100 }) as unknown as SubscriptionListResult
      const list = res.list || res.data?.list || []
      setMpList(list.map(item => ({ mp_id: item.mp_id, mp_name: item.mp_name || item.mp_id })))
    } catch (error) {
      console.error(t('subscriptions.messages.fetchFailed'), error)
    }
  }

  const loadArticles = async () => {
    setLoading(true)
    try {
      const res = await getArticles({
        page: pagination.current - 1,
        pageSize: pagination.pageSize,
        search: searchText,
        mp_id: mpId || undefined
      }) as unknown as ArticleListResult
      let list: Article[] = []
      let total = 0
      if (Array.isArray(res)) { list = res; total = res.length }
      else if (res && typeof res === 'object') {
        list = (res as any)?.list || (res as any)?.data?.list || []
        total = (res as any)?.total || (res as any)?.data?.total || 0
      }
      const visibleList = hideAiFiltered ? list.filter(item => item.ai_filter_status !== 'hide') : list
      setArticles(visibleList)
      setPagination(prev => ({ ...prev, total }))
      setSelectedRowKeys(prev => prev.filter(id => visibleList.some(item => String(item.id) === id)))
    } catch (error: any) {
      toast({ variant: "destructive", title: t('common.error'), description: error.message || t('articles.messages.fetchFailed') })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadMpList() }, [])
  useEffect(() => { loadArticles() }, [pagination.current, pagination.pageSize, searchText, mpId, hideAiFiltered])
  useEffect(() => {
    setJumpPageInput(String(pagination.current))
  }, [pagination.current])
  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(AI_FILTER_TASK_STORAGE_KEY)
      if (!raw) return
      const savedTask = JSON.parse(raw) as AiFilterTaskState
      if (savedTask?.pendingIds?.length) {
        setAiFilterTask({
          ...savedTask,
          status: savedTask.status === 'completed' ? 'paused' : savedTask.status,
          source: 'saved',
          currentBatchIds: []
        })
      } else {
        window.localStorage.removeItem(AI_FILTER_TASK_STORAGE_KEY)
      }
    } catch {
      window.localStorage.removeItem(AI_FILTER_TASK_STORAGE_KEY)
    }
  }, [])

  const persistAiFilterTask = (task: AiFilterTaskState | null) => {
    if (!task || !task.pendingIds.length || task.status === 'completed') {
      window.localStorage.removeItem(AI_FILTER_TASK_STORAGE_KEY)
      return
    }
    window.localStorage.setItem(AI_FILTER_TASK_STORAGE_KEY, JSON.stringify({
      ...task,
      currentBatchIds: []
    }))
  }

  const finalizeAiFilterTask = async (task: AiFilterTaskState) => {
    setAiFiltering(false)
    if (task.status === 'completed') {
      window.localStorage.removeItem(AI_FILTER_TASK_STORAGE_KEY)
      toast({
        title: t('common.success'),
        description: t('articles.aiFilter.analyzeSuccess', {
          hidden: task.hidden,
          keep: task.keep,
          maybe: task.maybe
        })
      })
      setSelectedRowKeys([])
      await loadArticles()
      return
    }

    persistAiFilterTask(task)
  }

  const runAiFilterTask = async (initialTask: AiFilterTaskState) => {
    aiFilterControlRef.current = 'running'
    setAiFiltering(true)

    let task = { ...initialTask, status: 'running' as const, errorMessage: undefined }
    setAiFilterTask(task)
    persistAiFilterTask(task)

    while (task.pendingIds.length > 0) {
      if (aiFilterControlRef.current === 'paused') {
        task = { ...task, status: 'paused', currentBatchIds: [] }
        setAiFilterTask(task)
        await finalizeAiFilterTask(task)
        return
      }

      if (aiFilterControlRef.current === 'stopped') {
        task = { ...task, status: 'stopped', currentBatchIds: [] }
        setAiFilterTask(task)
        await finalizeAiFilterTask(task)
        return
      }

      const batchIds = task.pendingIds.slice(0, AI_FILTER_BATCH_SIZE)
      task = { ...task, currentBatchIds: batchIds }
      setAiFilterTask(task)

      try {
        const res = await analyzeArticleAiFilter(batchIds)
        const data = (res as any)?.data || res
        const summary = (data as ArticleAiFilterAnalyzeResult)?.summary || {}

        task = {
          ...task,
          processed: task.processed + batchIds.length,
          hidden: task.hidden + (summary.hidden || 0),
          keep: task.keep + (summary.keep || 0),
          maybe: task.maybe + (summary.maybe || 0),
          pendingIds: task.pendingIds.slice(batchIds.length),
          currentBatchIds: [],
        }

        setAiFilterTask(task)
        persistAiFilterTask(task)
      } catch (error: any) {
        task = {
          ...task,
          status: 'error',
          currentBatchIds: [],
          errorMessage: error?.response?.data?.message || error?.message || t('articles.aiFilter.analyzeFailed')
        }
        setAiFilterTask(task)
        await finalizeAiFilterTask(task)
        toast({
          variant: 'destructive',
          title: t('common.error'),
          description: task.errorMessage
        })
        return
      }
    }

    task = {
      ...task,
      status: 'completed',
      currentBatchIds: [],
      pendingIds: []
    }
    setAiFilterTask(task)
    await finalizeAiFilterTask(task)
  }

  const processedArticleHtml = (record: { content?: string }) => {
    const raw = record?.content
    if (!raw) return ''
    return String(raw)
      .replace(/(<img[^>]*src=["'])(?!\/static\/res\/logo\/)(https?:\/\/(?:mmbiz\.qpic\.cn|mmbiz\.qlogo\.cn|mmecoa\.qpic\.cn|wx\.qlogo\.cn|thirdwx\.qlogo\.cn)\/[^"']*)/g, '$1/static/res/logo/$2')
      .replace(/<img([^>]*)width=["'][^"']*["']([^>]*)>/g, '<img$1$2>')
  }

  const viewArticle = async (article: Article, actionType: number = 0) => {
    setArticleModalVisible(true)
    setArticleDetailLoading(true)
    try {
      const res = await getArticleDetail(article.id, actionType)
      const articleData = (res as any)?.data || res
      if (articleData) {
        setCurrentArticle({
          ...article,
          ...articleData,
          mp_name: articleData.mp_name || article.mp_name,
          content: processedArticleHtml(articleData),
        } as Article)
      }
    } catch (error: any) {
      console.error(t('articles.messages.fetchDetailFailed'), error)
      toast({
        variant: 'destructive',
        title: t('common.error'),
        description: error?.message || t('articles.messages.fetchDetailFailed'),
      })
      setArticleModalVisible(false)
    } finally {
      setArticleDetailLoading(false)
    }
  }

  /** 标签等变更后刷新已打开的阅读抽屉（列表走 loadArticles；详情无列表缓存但可合并 tag_names） */
  const refreshOpenArticleDetail = async () => {
    if (!articleModalVisibleRef.current || !currentArticleRef.current) return
    const art = currentArticleRef.current
    setArticleDetailLoading(true)
    try {
      const res = await getArticleDetail(art.id as any, 0)
      const articleData = (res as any)?.data || res
      if (articleData) {
        setCurrentArticle({
          ...art,
          ...articleData,
          mp_name: articleData.mp_name || art.mp_name,
          content: processedArticleHtml(articleData),
        } as Article)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setArticleDetailLoading(false)
    }
  }

  const handleEdit = (article: Article) => {
    setEditingArticle(article)
    setEditFormData({ title: article.title || '', description: (article as any).description || '', url: article.link || (article as any).url || '', pic_url: (article as any).pic_url || '' })
    setEditDialogOpen(true)
  }

  const handleSaveEdit = async () => {
    if (!editingArticle) return
    try {
      await updateArticle(editingArticle.id, editFormData)
      toast({ title: t('common.success'), description: t('articles.messages.updateSuccess') })
      setEditDialogOpen(false); setEditingArticle(null); loadArticles()
    } catch (error: any) {
      toast({ variant: "destructive", title: t('common.error'), description: error.message || t('articles.messages.updateFailed') })
    }
  }

  const handleDelete = async (id: string | number) => { setDeleteTargetId(id); setDeleteDialogOpen(true) }
  const confirmDelete = async () => {
    if (!deleteTargetId) return
    try {
      await deleteArticleApi(deleteTargetId as any)
      toast({ title: t('common.success'), description: t('articles.messages.deleteSuccess') })
      setDeleteDialogOpen(false); setDeleteTargetId(null); loadArticles()
    } catch (error: any) { toast({ variant: "destructive", title: t('common.error'), description: error.message || t('articles.messages.deleteFailed') }) }
  }

  const openTagExtract = (kind: 'selected' | 'page' | 'all' | 'missing') => {
    if (kind === 'selected' && selectedRowKeys.length === 0) {
      toast({ variant: "destructive", title: t('common.warning'), description: t('articles.tagExtract.selectArticlesFirst') })
      return
    }
    if (kind === 'page' && articles.length === 0) {
      toast({ variant: "destructive", title: t('common.warning'), description: t('common.noData') })
      return
    }
    missingPollAbortRef.current = false
    setMissingTagJob(null)
    setTagExtractKind(kind)
    setTagExtractOpen(true)
  }

  const confirmTagExtract = async () => {
    if (!tagExtractKind) return

    if (tagExtractKind === 'missing') {
      setTagExtracting(true)
      setMissingTagJob(null)
      try {
        const res = await startMissingTagsJob() as any
        const data = res?.data ?? res
        if (!data?.job_id) {
          toast({ title: t('common.success'), description: data?.message || t('common.noData') })
          setTagExtractOpen(false)
          setTagExtractKind(null)
          return
        }
        const total = Number(data.total) || 0
        setMissingTagJob({
          job_id: data.job_id,
          total,
          processed: 0,
          success_count: 0,
          error_count: 0,
          status: 'running',
        })
        // eslint-disable-next-line no-constant-condition
        while (true) {
          if (missingPollAbortRef.current) break
          await new Promise((r) => setTimeout(r, 1200))
          if (missingPollAbortRef.current) break
          const st = (await getMissingTagsJobStatus(data.job_id)) as any
          const d = st?.data ?? st
          setMissingTagJob({
            job_id: data.job_id,
            total: Number(d.total) ?? total,
            processed: Number(d.processed) ?? 0,
            success_count: d.success_count,
            error_count: d.error_count,
            status: d.status,
            message: d.message,
            elapsed_seconds: d.elapsed_seconds ?? null,
          })
          if (d.status === 'done' || d.status === 'error') {
            if (d.status === 'error') {
              toast({ variant: 'destructive', title: t('common.error'), description: d.message || t('articles.tagExtract.failed') })
            } else {
              toast({ title: t('common.success'), description: d.message || t('articles.tagExtract.success') })
            }
            await loadArticles()
            await refreshOpenArticleDetail()
            break
          }
        }
        if (!missingPollAbortRef.current) {
          setTagExtractOpen(false)
          setTagExtractKind(null)
          setMissingTagJob(null)
        }
      } catch (error: any) {
        toast({
          variant: 'destructive',
          title: t('common.error'),
          description: error?.response?.data?.message || error?.message || t('articles.tagExtract.failed'),
        })
        setMissingTagJob(null)
      } finally {
        setTagExtracting(false)
      }
      return
    }

    setTagExtracting(true)
    try {
      let payload: string[]
      if (tagExtractKind === 'all') payload = ['__all__']
      else if (tagExtractKind === 'selected') payload = selectedRowKeys.map(String)
      else payload = articles.map(a => String(a.id))

      const res = await reExtractTags(payload)
      const data = (res as any)?.data || res
      toast({ title: t('common.success'), description: data?.message || t('articles.tagExtract.success') })
      await loadArticles()
      await refreshOpenArticleDetail()
      if (tagExtractKind === 'selected') setSelectedRowKeys([])
      setTagExtractOpen(false)
      setTagExtractKind(null)
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: t('common.error'),
        description: error?.response?.data?.message || error?.message || t('articles.tagExtract.failed'),
      })
    } finally {
      setTagExtracting(false)
    }
  }

  const startAiFilterTask = async (ids: string[], source: 'selection' | 'page' | 'saved' | 'full') => {
    if (ids.length === 0) {
      toast({ variant: "destructive", title: t('common.warning'), description: t('articles.aiFilter.selectFirst') })
      return
    }

    const nextTask: AiFilterTaskState = {
      total: ids.length,
      processed: 0,
      hidden: 0,
      keep: 0,
      maybe: 0,
      pendingIds: ids,
      currentBatchIds: [],
      status: 'idle',
      source
    }
    setAiFilterTask(nextTask)
    setAiFilterDialogOpen(true)
    runAiFilterTask(nextTask)
  }

  const confirmAiFilterAll = async () => {
    if (aiFilterTask?.pendingIds?.length && aiFilterTask.status !== 'completed') {
      setAiFilterAllConfirmOpen(false)
      setAiFilterDialogOpen(true)
      return
    }
    setAiFiltering(true)
    try {
      const res = (await getAllArticleIdsForAiFilter()) as any
      const data = res?.data ?? res
      const ids: string[] = Array.isArray(data?.ids) ? data.ids.map(String) : []
      if (ids.length === 0) {
        toast({ title: t('common.success'), description: '没有需要过滤的文章' })
        return
      }
      setAiFilterAllConfirmOpen(false)
      setSelectedRowKeys([])
      startAiFilterTask(ids, 'full')
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: t('common.error'),
        description: error?.response?.data?.message || error?.message || t('articles.aiFilter.analyzeFailed'),
      })
    } finally {
      setAiFiltering(false)
    }
  }

  const handleAiFilter = async (scope: 'selected' | 'page' | 'unfiltered') => {
    if (aiFilterTask?.pendingIds?.length && aiFilterTask.status !== 'completed') {
      setAiFilterDialogOpen(true)
      return
    }

    if (scope === 'unfiltered') {
      setAiFiltering(true)
      try {
        const res = await getUnfilteredArticleIds() as any
        const data = res?.data || res
        const ids: string[] = data?.ids || []
        if (ids.length === 0) {
          toast({ title: t('common.success'), description: '没有未过滤的文章' })
          setAiFiltering(false)
          return
        }
        setAiFiltering(false)
        return startAiFilterTask(ids, 'page')
      } catch (error: any) {
        toast({ variant: 'destructive', title: t('common.error'), description: error?.response?.data?.message || error?.message || t('articles.aiFilter.analyzeFailed') })
        setAiFiltering(false)
      }
      return
    }

    if (scope === 'selected') {
      if (selectedRowKeys.length === 0) {
        toast({ variant: "destructive", title: t('common.warning'), description: t('articles.messages.selectFirst') })
        return
      }
      return startAiFilterTask([...selectedRowKeys], 'selection')
    }

    // scope === 'page'
    if (articles.length === 0) {
      toast({ variant: "destructive", title: t('common.warning'), description: t('articles.aiFilter.selectFirst') })
      return
    }
    return startAiFilterTask(articles.map(a => String(a.id)), 'page')
  }

  const handleResumeAiFilterTask = () => {
    if (!aiFilterTask || !aiFilterTask.pendingIds.length) return
    setAiFilterDialogOpen(true)
    runAiFilterTask({ ...aiFilterTask, status: 'running' })
  }

  const handlePauseAiFilterTask = () => {
    aiFilterControlRef.current = 'paused'
  }

  const handleStopAiFilterTask = () => {
    aiFilterControlRef.current = 'stopped'
  }

  const handleCloseAiFilterDialog = (open: boolean) => {
    if (!open && aiFiltering) return
    setAiFilterDialogOpen(open)
  }

  const handleRestoreAiFilter = async (article: Article) => {
    try {
      await restoreArticleAiFilter([article.id])
      toast({ title: t('common.success'), description: t('articles.aiFilter.restoreSuccess') })
      loadArticles()
    } catch (error: any) {
      toast({ variant: "destructive", title: t('common.error'), description: error?.response?.data?.message || error?.message || t('articles.aiFilter.restoreFailed') })
    }
  }

  const handleToggleArticleStatus = async (article: Article) => {
    const nextStatus = article.status === 1 ? 2 : 1
    const articleId = String(article.id)
    setStatusUpdatingIds(prev => [...prev, articleId])
    setArticles(prev => prev.map(item => (
      String(item.id) === articleId ? { ...item, status: nextStatus } : item
    )))
    try {
      await updateArticle(article.id, { status: nextStatus })
      toast({
        title: t('common.success'),
        description: nextStatus === 1 ? t('articles.status.enabled') : t('articles.status.disabled'),
      })
    } catch (error: any) {
      setArticles(prev => prev.map(item => (
        String(item.id) === articleId ? { ...item, status: article.status } : item
      )))
      toast({ variant: "destructive", title: t('common.error'), description: error.message || t('articles.messages.updateFailed') })
    } finally {
      setStatusUpdatingIds(prev => prev.filter(id => id !== articleId))
    }
  }

  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) { toast({ variant: "destructive", title: t('common.warning'), description: t('articles.messages.selectFirst') }); return }
    setBatchDeleteDialogOpen(true)
  }

  const confirmBatchDelete = async () => {
    try {
      await Promise.all(selectedRowKeys.map(id => deleteArticleApi(id as any)))
      toast({ title: t('common.success'), description: t('articles.messages.batchDeleteSuccess', { count: selectedRowKeys.length }) })
      setSelectedRowKeys([]); setBatchDeleteDialogOpen(false); loadArticles()
    } catch (error: any) { toast({ variant: "destructive", title: t('common.error'), description: error.message || t('articles.messages.batchDeleteFailed') }) }
  }

  const openRssFeed = (format: string) => {
    const baseUrl = window.location.origin
    const feedUrl = mpId ? `${baseUrl}/feed/mp/${mpId}.${format}` : `${baseUrl}/feed/all.${format}`
    window.open(feedUrl, '_blank')
  }

  const handleExportClick = () => {
    const selectedIds = (selectedRowKeys || []).slice()
    let currentMpId = mpId || ''
    let mpName = t('common.all') || '全部'
    if (selectedIds.length > 0) {
      const selectedArticles = articles.filter(art => selectedRowKeys.includes(String(art.id)))
      if (selectedArticles.length > 0) {
        const mpIds = selectedArticles.map(art => (art as any).mp_id).filter(Boolean)
        const uniqueMpIds = [...new Set(mpIds)]
        if (uniqueMpIds.length === 1) {
          currentMpId = uniqueMpIds[0]
          const currentMp = mpList.find(mp => mp.mp_id === currentMpId)
          mpName = currentMp?.mp_name || selectedArticles[0].mp_name || '全部'
        } else { currentMpId = 'all'; mpName = '全部' }
      }
    } else {
      if (!currentMpId) currentMpId = 'all'
      const currentMp = mpList.find(mp => mp.mp_id === currentMpId)
      mpName = currentMp?.mp_name || '全部'
    }
    exportModalRef.current?.show(currentMpId, selectedIds, mpName)
  }

  const toggleRowSelection = (id: string | number) => {
    const idStr = String(id)
    setSelectedRowKeys(prev => prev.includes(idStr) ? prev.filter(key => key !== idStr) : [...prev, idStr])
  }

  const toggleAllSelection = () => {
    if (selectedRowKeys.length === articles.length) setSelectedRowKeys([])
    else setSelectedRowKeys(articles.map(a => String(a.id)))
  }

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
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t('articles.title')}</h1>
          <p className="text-sm text-muted-foreground mt-1">{t('articles.subtitle') || t('articles.title')}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={handleExportClick} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            {t('articles.export')}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <Wifi className="h-4 w-4 mr-2" />
                RSS
                <ChevronDown className="h-4 w-4 ml-1" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => openRssFeed('atom')}>ATOM</DropdownMenuItem>
              <DropdownMenuItem onClick={() => openRssFeed('rss')}>RSS</DropdownMenuItem>
              <DropdownMenuItem onClick={() => openRssFeed('json')}>JSON</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Filter Card */}
      <Card>
        <CardContent className="p-6">
          <div className="space-y-4">
            <div className="flex flex-col md:flex-row items-center gap-4">
              <div className="relative flex-1 w-full">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={t('common.search')}
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="flex items-center gap-3 w-full md:w-auto">
                <Select
                  value={mpId || "__all__"}
                  onValueChange={(value) => setMpId(value === "__all__" ? "" : value)}
                >
                  <SelectTrigger className="w-full md:w-[200px]">
                    <SelectValue placeholder={t('common.all')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">{t('common.all')}</SelectItem>
                    {mpList.map(mp => (
                      <SelectItem key={mp.mp_id} value={mp.mp_id}>
                        {mp.mp_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => { setSearchText(''); setMpId(''); }}
                >
                  <RotateCcw className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 rounded-lg border bg-muted/30 px-4 py-3">
              <div className="flex items-center gap-3">
                <Switch checked={hideAiFiltered} onCheckedChange={setHideAiFiltered} />
                <div>
                  <div className="text-sm font-medium">{t('articles.aiFilter.hideLabel')}</div>
                  <div className="text-xs text-muted-foreground">{t('articles.aiFilter.hideDesc')}</div>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {selectedRowKeys.length > 0 ? (
                  <span className="text-sm text-muted-foreground">
                    已选 {selectedRowKeys.length} 篇
                  </span>
                ) : null}
                <span className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
                  <Sparkles className="h-4 w-4" />
                  AI增强
                </span>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" disabled={aiFiltering || loading}>
                      {aiFiltering && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                      文章过滤
                      <ChevronDown className="h-4 w-4 ml-1" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="min-w-[220px]">
                    <DropdownMenuItem onClick={() => handleAiFilter('selected')} disabled={!selectedRowKeys.length || aiFiltering}>
                      {t('articles.aiFilter.filterSelected')}
                      {selectedRowKeys.length > 0 ? ` (${selectedRowKeys.length})` : ''}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleAiFilter('page')} disabled={!articles.length || aiFiltering}>
                      {t('articles.aiFilter.filterPage')}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleAiFilter('unfiltered')} disabled={aiFiltering}>
                      {t('articles.aiFilter.filterUnfiltered')}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => setAiFilterAllConfirmOpen(true)}
                      disabled={aiFiltering || loading}
                      className="text-destructive focus:text-destructive"
                    >
                      {t('articles.aiFilter.filterAll')}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                {aiFilterTask?.pendingIds?.length ? (
                  <Button variant="secondary" onClick={handleResumeAiFilterTask} disabled={aiFiltering || loading}>
                    {t('articles.aiFilter.resume')}
                  </Button>
                ) : null}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" disabled={tagExtracting || loading}>
                      {tagExtracting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                      {t('articles.tagExtract.menu')}
                      <ChevronDown className="h-4 w-4 ml-1" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="min-w-[220px]">
                    <DropdownMenuItem onClick={() => openTagExtract('selected')} disabled={!selectedRowKeys.length || tagExtracting}>
                      {t('articles.tagExtract.selected')}
                      {selectedRowKeys.length > 0 ? ` (${selectedRowKeys.length})` : ''}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => openTagExtract('page')} disabled={!articles.length || tagExtracting}>
                      {t('articles.tagExtract.page')}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => openTagExtract('missing')} disabled={tagExtracting}>
                      {t('articles.tagExtract.missing')}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => openTagExtract('all')} disabled={tagExtracting} className="text-destructive focus:text-destructive">
                      {t('articles.tagExtract.all')}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                {selectedRowKeys.length > 0 ? (
                  <Button variant="destructive" onClick={handleBatchDelete}>
                    <Trash2 className="h-4 w-4 mr-2" />
                    {t('articles.batchDelete')}
                  </Button>
                ) : null}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedRowKeys.length === articles.length && articles.length > 0}
                      onCheckedChange={toggleAllSelection}
                    />
                  </TableHead>
                  <TableHead>{t('articles.columns.title') || '标题'}</TableHead>
                  <TableHead>{t('articles.columns.source') || '来源'}</TableHead>
                  <TableHead>{t('articles.columns.tags') || '标签'}</TableHead>
                  <TableHead>{t('articles.columns.filterTags')}</TableHead>
                  <TableHead>{t('articles.columns.publishTime') || '发布时间'}</TableHead>
                  <TableHead className="text-right">{t('articles.columns.actions') || t('common.actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow><TableCell colSpan={7} className="h-24 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></TableCell></TableRow>
                ) : articles.length === 0 ? (
                  <TableRow><TableCell colSpan={7} className="h-24 text-center text-muted-foreground">{t('common.noData')}</TableCell></TableRow>
                ) : (
                  articles.map((article) => {
                    const tags = (article as any).tag_names || (article as any).topic_names || ((article as any).tags ? (article as any).tags.map((t: any) => t.name || t) : []) || []
                    const statusBadgeClassName = article.status === 1
                      ? "gap-1 cursor-pointer select-none border border-emerald-600 bg-emerald-600 text-white hover:bg-emerald-700 hover:text-white"
                      : "gap-1 cursor-pointer select-none border border-zinc-300 bg-zinc-100 text-zinc-700 hover:bg-zinc-200 hover:text-zinc-800 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700"
                    const time = (article as any).publish_time
                    let timeDisplay = '-'
                    if (time || time === 0) {
                      if (typeof time === 'number') {
                        const timestamp = time
                        const adjustedTimestamp = timestamp.toString().length <= 10 ? timestamp * 1000 : timestamp
                        const date = dayjs(adjustedTimestamp)
                        if (date.isValid() && date.year() >= 1970 && date.year() < 2100) timeDisplay = date.format('YYYY-MM-DD')
                      } else timeDisplay = dayjs(time).format('YYYY-MM-DD')
                    }

                    return (
                      <TableRow key={article.id}>
                        <TableCell>
                          <Checkbox
                            checked={selectedRowKeys.includes(String(article.id))}
                            onCheckedChange={() => toggleRowSelection(article.id)}
                          />
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            <a
                              href="#"
                              onClick={(e) => { e.preventDefault(); viewArticle(article) }}
                              className="text-emerald-600 hover:underline break-words cursor-pointer font-medium"
                            >
                              {article.title}
                            </a>
                            <div className="flex flex-wrap items-center gap-2">
                              <button
                                type="button"
                                onClick={() => handleToggleArticleStatus(article)}
                                disabled={statusUpdatingIds.includes(String(article.id))}
                                className="inline-flex items-center"
                              >
                                <Badge
                                  variant="outline"
                                  className={statusBadgeClassName}
                                >
                                  {statusUpdatingIds.includes(String(article.id)) ? (
                                    <Loader2 className="h-3 w-3 animate-spin" />
                                  ) : article.status === 1 ? (
                                    <CheckCircle2 className="h-3 w-3" />
                                  ) : (
                                    <Ban className="h-3 w-3" />
                                  )}
                                  {article.status === 1 ? t('common.enabled') : t('common.disabled')}
                                </Badge>
                              </button>
                              {article.ai_filter_status && article.ai_filter_status !== 'keep' && (
                                <Badge
                                  variant={article.ai_filter_status === 'hide' ? 'destructive' : 'secondary'}
                                  className="gap-1"
                                >
                                  {article.ai_filter_status === 'hide' ? <EyeOff className="h-3 w-3" /> : <Info className="h-3 w-3" />}
                                  {t(`articles.aiFilter.status.${article.ai_filter_status}`)}
                                </Badge>
                              )}
                              <button
                                onClick={() => handleEdit(article)}
                                className="text-xs text-muted-foreground hover:text-primary"
                              >
                                <Edit className="h-3 w-3" />
                              </button>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>{article.mp_name}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {tags.length === 0 ? (
                              <Badge variant="outline">{t('common.noData')}</Badge>
                            ) : (
                              tags.slice(0, 3).map((tag: string, idx: number) => (
                                <Badge key={idx} variant="outline">{tag}</Badge>
                              ))
                            )}
                            {tags.length > 3 && <span className="text-xs text-muted-foreground">+{tags.length - 3}</span>}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1 max-w-[220px]">
                            {!article.ai_filter_status ? (
                              <span className="text-xs text-muted-foreground">—</span>
                            ) : (
                              <Badge
                                variant={
                                  article.ai_filter_status === 'hide'
                                    ? 'destructive'
                                    : article.ai_filter_status === 'maybe'
                                      ? 'secondary'
                                      : 'outline'
                                }
                                className="font-normal"
                              >
                                {t(`articles.aiFilter.status.${article.ai_filter_status}`)}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{timeDisplay}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1">
                            {article.ai_filter_status === 'hide' && (
                              <Button variant="ghost" size="sm" onClick={() => handleRestoreAiFilter(article)}>
                                <Undo2 className="h-4 w-4" />
                              </Button>
                            )}
                            <Button variant="ghost" size="sm" onClick={() => handleDelete(article.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 border-t">
              <div className="text-sm text-muted-foreground">
                {t('common.page', { current: pagination.current, total: totalPages, count: pagination.total })}
              </div>
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
                  {t('common.previousPage')}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPagination(prev => ({ ...prev, current: Math.min(totalPages, prev.current + 1) }))}
                  disabled={pagination.current === totalPages}
                >
                  {t('common.nextPage')}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('articles.delete')}</DialogTitle>
            <DialogDescription>{t('common.confirm')}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>{t('common.cancel')}</Button>
            <Button variant="destructive" onClick={confirmDelete}>{t('common.delete')}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Batch Delete Confirmation Dialog */}
      <Dialog open={batchDeleteDialogOpen} onOpenChange={setBatchDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('articles.batchDelete')}</DialogTitle>
            <DialogDescription>{t('common.confirm')}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBatchDeleteDialogOpen(false)}>{t('common.cancel')}</Button>
            <Button variant="destructive" onClick={confirmBatchDelete}>{t('common.delete')}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('articles.edit')}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium">{t('articles.columns.title') || '标题'}</label>
              <Input
                value={editFormData.title}
                onChange={(e) => setEditFormData({ ...editFormData, title: e.target.value })}
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-sm font-medium">{t('subscriptions.description')}</label>
              <Textarea
                value={editFormData.description}
                onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                className="mt-1"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>{t('common.cancel')}</Button>
            <Button onClick={handleSaveEdit}>{t('common.save')}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={tagExtractOpen}
        onOpenChange={(open) => {
          if (!open) {
            missingPollAbortRef.current = true
            setTagExtractOpen(false)
            setTagExtractKind(null)
            setMissingTagJob(null)
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {tagExtractKind === 'all'
                ? t('articles.tagExtract.confirmAllTitle')
                : tagExtractKind === 'missing'
                  ? t('articles.tagExtract.confirmMissingTitle')
                  : tagExtractKind === 'page'
                    ? t('articles.tagExtract.confirmPageTitle')
                    : t('articles.tagExtract.confirmSelectedTitle')}
            </DialogTitle>
            <DialogDescription className="whitespace-pre-line">
              {tagExtractKind === 'all'
                ? t('articles.tagExtract.confirmAllDesc')
                : tagExtractKind === 'missing'
                  ? t('articles.tagExtract.confirmMissingDesc')
                  : tagExtractKind === 'page'
                    ? t('articles.tagExtract.confirmPageDesc', { count: articles.length })
                    : t('articles.tagExtract.confirmSelectedDesc', { count: selectedRowKeys.length })}
            </DialogDescription>
          </DialogHeader>
          {tagExtractKind === 'missing' && missingTagJob && missingTagJob.status === 'running' && (
            <div className="space-y-3 py-2">
              <div className="flex items-center justify-between text-sm">
                <span>{t('articles.tagExtract.missingProgressLabel')}</span>
                <span className="tabular-nums font-medium">
                  {t('articles.tagExtract.missingProgressCount', {
                    processed: missingTagJob.processed,
                    total: missingTagJob.total,
                  })}
                </span>
              </div>
              <div className="h-2 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-300"
                  style={{
                    width: `${missingTagJob.total > 0 ? (missingTagJob.processed / missingTagJob.total) * 100 : 0}%`,
                  }}
                />
              </div>
              {missingTagJob.elapsed_seconds != null && (
                <p className="text-xs text-muted-foreground">
                  {t('articles.tagExtract.missingElapsed', { seconds: missingTagJob.elapsed_seconds })}
                </p>
              )}
            </div>
          )}
          {tagExtracting && tagExtractKind !== 'missing' && (
            <div className="flex items-center gap-3 py-4">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
              <span className="text-sm text-muted-foreground">
                {tagExtractKind === 'all'
                  ? t('articles.tagExtract.allRunning')
                  : tagExtractKind === 'page'
                    ? t('articles.tagExtract.pageRunning')
                    : t('articles.tagExtract.selectedRunning')}
              </span>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                missingPollAbortRef.current = true
                setTagExtractOpen(false)
                setTagExtractKind(null)
                setMissingTagJob(null)
                setTagExtracting(false)
              }}
            >
              {t('common.cancel')}
            </Button>
            <Button
              onClick={confirmTagExtract}
              disabled={
                tagExtracting ||
                (tagExtractKind === 'missing' && !!missingTagJob)
              }
            >
              {tagExtracting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {tagExtractKind === 'missing' && missingTagJob
                ? t('articles.tagExtract.missingRunning')
                : t('common.confirm')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={aiFilterAllConfirmOpen}
        onOpenChange={(open) => {
          if (!open && aiFiltering) return
          setAiFilterAllConfirmOpen(open)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('articles.aiFilter.confirmAllTitle')}</DialogTitle>
            <DialogDescription className="whitespace-pre-line">
              {t('articles.aiFilter.confirmAllDesc')}
            </DialogDescription>
          </DialogHeader>
          {aiFiltering && (
            <div className="flex items-center gap-3 py-4">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
              <span className="text-sm text-muted-foreground">{t('articles.aiFilter.allRunning')}</span>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setAiFilterAllConfirmOpen(false)}
              disabled={aiFiltering}
            >
              {t('common.cancel')}
            </Button>
            <Button
              variant="destructive"
              onClick={() => void confirmAiFilterAll()}
              disabled={aiFiltering}
            >
              {aiFiltering && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {t('common.confirm')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={aiFilterDialogOpen} onOpenChange={handleCloseAiFilterDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('articles.aiFilter.taskTitle')}</DialogTitle>
            <DialogDescription>{t('articles.aiFilter.taskDesc')}</DialogDescription>
          </DialogHeader>
          {aiFilterTask ? (
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>{t('articles.aiFilter.progress')}</span>
                  <span>{aiFilterTask.processed} / {aiFilterTask.total}</span>
                </div>
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${aiFilterTask.total > 0 ? (aiFilterTask.processed / aiFilterTask.total) * 100 : 0}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 text-sm">
                <div className="rounded-lg border p-3">
                  <div className="text-muted-foreground">{t('articles.aiFilter.status.hide')}</div>
                  <div className="text-lg font-semibold">{aiFilterTask.hidden}</div>
                </div>
                <div className="rounded-lg border p-3">
                  <div className="text-muted-foreground">{t('articles.aiFilter.status.keep')}</div>
                  <div className="text-lg font-semibold">{aiFilterTask.keep}</div>
                </div>
                <div className="rounded-lg border p-3">
                  <div className="text-muted-foreground">{t('articles.aiFilter.status.maybe')}</div>
                  <div className="text-lg font-semibold">{aiFilterTask.maybe}</div>
                </div>
              </div>

              <div className="rounded-lg border bg-muted/30 p-3 text-sm text-muted-foreground">
                {aiFiltering
                  ? t('articles.aiFilter.runningHint')
                  : aiFilterTask.status === 'paused'
                    ? t('articles.aiFilter.pausedHint', { count: aiFilterTask.pendingIds.length })
                    : aiFilterTask.status === 'stopped'
                      ? t('articles.aiFilter.stoppedHint', { count: aiFilterTask.pendingIds.length })
                      : aiFilterTask.status === 'completed'
                        ? t('articles.aiFilter.completedHint')
                        : aiFilterTask.status === 'error'
                          ? (aiFilterTask.errorMessage || t('articles.aiFilter.analyzeFailed'))
                          : t('articles.aiFilter.idleHint')}
              </div>
            </div>
          ) : null}
          <DialogFooter>
            <Button variant="outline" onClick={() => setAiFilterDialogOpen(false)} disabled={aiFiltering}>
              {aiFilterTask?.status === 'completed' ? t('common.done') : t('common.cancel')}
            </Button>
            {aiFiltering ? (
              <>
                <Button variant="outline" onClick={handlePauseAiFilterTask}>
                  {t('articles.aiFilter.pause')}
                </Button>
                <Button variant="destructive" onClick={handleStopAiFilterTask}>
                  {t('articles.aiFilter.stop')}
                </Button>
              </>
            ) : aiFilterTask?.pendingIds?.length ? (
              <Button onClick={handleResumeAiFilterTask}>
                {t('articles.aiFilter.resume')}
              </Button>
            ) : null}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Drawer open={articleModalVisible} onOpenChange={setArticleModalVisible}>
        <DrawerContent className="!mt-6 flex h-[min(90vh,100dvh)] max-h-[95vh] flex-col overflow-hidden p-0 sm:max-w-2xl sm:mx-auto">
          <DrawerHeader className="shrink-0 space-y-1 border-b border-border px-4 pb-3 pt-2 text-left">
            <DrawerTitle id="article-reader-title" className="pr-2 leading-snug line-clamp-3">
              {currentArticle?.title || ''}
            </DrawerTitle>
          </DrawerHeader>
          <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden px-4 pb-6">
            {articleDetailLoading ? (
              <div className="flex justify-center py-16">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : currentArticle ? (
              <>
                <div className="mb-4 text-sm text-muted-foreground flex flex-wrap gap-x-4 gap-y-2">
                  <a
                    href={(currentArticle as any).url || currentArticle.link || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline text-primary"
                  >
                    {t('articles.reader.viewOriginal')}
                  </a>
                  <span>
                    {t('articles.reader.updatedAt')}：{formatDateTime((currentArticle as any).created_at || currentArticle.created_at)}
                  </span>
                  <button
                    type="button"
                    className="hover:underline text-primary"
                    onClick={() => viewArticle(currentArticle, -1)}
                  >
                    {t('articles.reader.prevArticle')}
                  </button>
                  <button
                    type="button"
                    className="hover:underline text-primary"
                    onClick={() => viewArticle(currentArticle, 1)}
                  >
                    {t('articles.reader.nextArticle')}
                  </button>
                </div>
                {(() => {
                  // content 在 viewArticle 里已做 processedArticleHtml，此处直接渲染
                  const html = (currentArticle as any).content != null ? String((currentArticle as any).content) : ''
                  const hasBody = html.replace(/&nbsp;|\s/g, '').length > 0
                  const desc = (currentArticle as any).description
                  if (hasBody) {
                    return (
                      <div
                        className="max-w-none break-words rounded-md border border-zinc-200 bg-white px-3 py-4 text-left text-neutral-900 shadow-sm [&_img]:max-w-full [&_img]:h-auto"
                        // 与 App 亮/暗无关：微信正文多为浅色内联样式，统一用纸感白底，避免暗色主题下整段「消失」
                        dangerouslySetInnerHTML={{ __html: html }}
                      />
                    )
                  }
                  if (desc && String(desc).replace(/\s/g, '').length > 0) {
                    return (
                      <div className="space-y-3 text-sm text-muted-foreground">
                        <p className="text-amber-600 dark:text-amber-500">
                          正文未入库，以下为摘要/描述。完整正文可点「{t('articles.reader.viewOriginal')}」，或使用接口重新拉取正文。
                        </p>
                        <div
                          className="max-w-none break-words rounded-md border bg-muted/40 p-3 text-foreground"
                          style={{ color: 'var(--foreground)' }}
                          dangerouslySetInnerHTML={{ __html: String(desc) }}
                        />
                      </div>
                    )
                  }
                  return (
                    <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
                      <p className="mb-2">当前没有可展示的正文（数据库中该篇 content 为空）。</p>
                      <p>
                        可点击上方「{t('articles.reader.viewOriginal')}」阅读；或确认采集已拉取全文。管理员可调用
                        <code className="mx-1 rounded bg-muted px-1">POST /api/v1/wx/articles/…/fetch_content</code>
                        重拉正文后刷新本页。
                      </p>
                    </div>
                  )
                })()}
              </>
            ) : null}
          </div>
        </DrawerContent>
      </Drawer>

      <ExportModal ref={exportModalRef} />
    </div>
  )
}

export default ArticleListPage
