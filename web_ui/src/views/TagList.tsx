import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'
import { ExportTags, ImportTags } from '@/api/export'
import { listTags, deleteTag, batchDeleteTags, updateTagStatus } from '@/api/tagManagement'
import type { Tag as TagType } from '@/types/tagManagement'
import { Download, Upload, Plus, Edit, Trash2, Loader2, Rss, Search, CheckCircle2, Ban } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { formatDateTime } from '@/utils/date'
import { useTranslation } from 'react-i18next'

const TagList: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [tags, setTags] = useState<TagType[]>([])
  const [allTags, setAllTags] = useState<TagType[]>([]) // 存储所有标签用于搜索
  const [searchText, setSearchText] = useState('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null)
  const [batchDeleteDialogOpen, setBatchDeleteDialogOpen] = useState(false)
  const [jumpPageInput, setJumpPageInput] = useState('1')
  const [statusUpdatingIds, setStatusUpdatingIds] = useState<string[]>([])
  const { toast } = useToast()

  const fetchTags = async () => {
    try {
      setLoading(true)
      // 获取所有标签用于搜索
      const allRes = await listTags({
        offset: 0,
        limit: 10000
      }) as unknown as { list?: TagType[]; total?: number }
      const allTagsData = allRes.list || []
      setAllTags(allTagsData)
      
      // 应用搜索过滤
      let filteredTags = allTagsData
      if (searchText.trim()) {
        filteredTags = allTagsData.filter(tag => 
          tag.name?.toLowerCase().includes(searchText.toLowerCase().trim())
        )
      }
      
      // 分页处理
      const total = filteredTags.length
      const start = (pagination.current - 1) * pagination.pageSize
      const end = start + pagination.pageSize
      const paginatedTags = filteredTags.slice(start, end)
      
      setTags(paginatedTags)
      setPagination(prev => ({ ...prev, total }))
    } catch (error) {
      toast({
        variant: "destructive",
        title: t('tags.messages.fetchFailed'),
        description: t('tags.messages.fetchFailed')
      })
    } finally {
      setLoading(false)
    }
  }

  // 当搜索文本改变时，重置到第一页
  useEffect(() => {
    if (pagination.current !== 1) {
      setPagination(prev => ({ ...prev, current: 1 }))
    }
  }, [searchText])

  useEffect(() => {
    fetchTags()
  }, [pagination.current, pagination.pageSize, searchText])

  useEffect(() => {
    setJumpPageInput(String(pagination.current))
  }, [pagination.current])

  const handleSearch = () => {
    // 搜索按钮点击，确保重置到第一页（如果不在第一页）
    if (pagination.current !== 1) {
      setPagination(prev => ({ ...prev, current: 1 }))
    } else {
      // 如果已经在第一页，手动触发搜索
      fetchTags()
    }
  }

  const handleDelete = (id: string) => {
    setDeleteTargetId(id)
    setDeleteDialogOpen(true)
  }

  const handleToggleStatus = async (tag: TagType) => {
    if (tag.status === 2) {
      toast({
        variant: "destructive",
        title: t('tags.messages.statusBlocked'),
        description: t('tags.messages.statusBlockedDesc')
      })
      return
    }

    const nextStatus = tag.status === 1 ? 0 : 1
    try {
      setStatusUpdatingIds(prev => [...prev, tag.id])
      setTags(prev => prev.map(item => item.id === tag.id ? { ...item, status: nextStatus } : item))
      setAllTags(prev => prev.map(item => item.id === tag.id ? { ...item, status: nextStatus } : item))
      await updateTagStatus(tag, nextStatus)
      toast({
        title: t('tags.messages.statusUpdateSuccess'),
        description: nextStatus === 1 ? t('common.enabled') : t('common.disabled')
      })
    } catch (error) {
      setTags(prev => prev.map(item => item.id === tag.id ? { ...item, status: tag.status } : item))
      setAllTags(prev => prev.map(item => item.id === tag.id ? { ...item, status: tag.status } : item))
      toast({
        variant: "destructive",
        title: t('tags.messages.statusUpdateFailed'),
        description: t('tags.messages.statusUpdateFailed')
      })
    } finally {
      setStatusUpdatingIds(prev => prev.filter(id => id !== tag.id))
    }
  }

  const confirmDelete = async () => {
    if (!deleteTargetId) return
    try {
      await deleteTag(deleteTargetId)
      setDeleteDialogOpen(false)
      setDeleteTargetId(null)
      toast({
        title: t('tags.messages.deleteSuccess'),
        description: t('tags.messages.deleteSuccess')
      })
      fetchTags()
    } catch (error) {
      toast({
        variant: "destructive",
        title: t('tags.messages.deleteFailed'),
        description: t('tags.messages.deleteFailed')
      })
    }
  }

  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) {
      toast({
        variant: "destructive",
        title: t('tags.messages.selectFirst'),
        description: t('tags.messages.selectFirst')
      })
      return
    }
    setBatchDeleteDialogOpen(true)
  }

  const confirmBatchDelete = async () => {
    try {
      await batchDeleteTags(selectedRowKeys)
      toast({
        title: t('tags.messages.batchDeleteSuccess', { count: selectedRowKeys.length }),
        description: t('tags.messages.batchDeleteSuccess', { count: selectedRowKeys.length })
      })
      setSelectedRowKeys([])
      setBatchDeleteDialogOpen(false)
      fetchTags()
    } catch (error) {
      toast({
        variant: "destructive",
        title: t('tags.messages.batchDeleteFailed'),
        description: t('tags.messages.batchDeleteFailed')
      })
    }
  }

  const exportTags = async () => {
    toast({
      title: t('tags.messages.exportGenerating'),
      description: t('tags.messages.exportGenerating')
    })
    try {
      const res = await ExportTags()
      const data = (res as any).data ?? res
      const blob = data instanceof Blob
        ? data
        : new Blob([data], { type: 'text/csv;charset=utf-8' })

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = '标签列表.csv'
      document.body.appendChild(a)
      a.click()

      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast({
        title: t('tags.messages.exportSuccess'),
        description: t('tags.messages.exportSuccess')
      })
    } catch (error: any) {
      console.error('导出标签失败:', error)
      const errorMessage = error?.message || t('tags.messages.exportFailed')
      toast({
        variant: "destructive",
        title: t('tags.messages.exportFailed'),
        description: errorMessage
      })
    }
  }

  const importTags = async () => {
    try {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.csv'

      input.onchange = async (e) => {
        const file = (e.target as HTMLInputElement).files?.[0]
        if (!file) return

        const formData = new FormData()
        formData.append('file', file)

        toast({
          title: t('tags.messages.importGenerating'),
          description: t('tags.messages.importGenerating')
        })
        try {
          const res = await ImportTags(formData)
          const data = (res as any).data ?? res
          toast({
            title: t('tags.messages.importSuccess'),
            description: data?.message || t('tags.messages.importSuccess')
          })
          fetchTags()
        } catch (importError: any) {
          const detail = importError.response?.data?.detail
          const errorMessage = (typeof detail === 'object' && detail.message) ? detail.message : (detail || t('tags.messages.importFailed'))
          toast({
            variant: "destructive",
            title: t('tags.messages.importFailed'),
            description: errorMessage
          })
          console.error('导入标签时发生错误:', importError)
        }
      }

      input.click()
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: t('tags.messages.filePickerFailed'),
        description: error?.message || t('tags.messages.filePickerFailed')
      })
    }
  }

  const toggleRowSelection = (id: string) => {
    setSelectedRowKeys(prev => 
      prev.includes(id) 
        ? prev.filter(key => key !== id)
        : [...prev, id]
    )
  }

  const toggleAllSelection = () => {
    if (selectedRowKeys.length === tags.length) {
      setSelectedRowKeys([])
    } else {
      setSelectedRowKeys(tags.map(t => t.id))
    }
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
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 text-foreground">
          标签管理
        </h1>
        <p className="text-muted-foreground text-sm">管理文章标签</p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle>标签列表</CardTitle>
            <CardDescription>管理文章标签和分类</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {selectedRowKeys.length > 0 && (
              <>
                <span className="text-sm text-muted-foreground">已选择 {selectedRowKeys.length} 项</span>
                <Button variant="destructive" onClick={handleBatchDelete}>
                  批量删除
                </Button>
              </>
            )}
            <Button variant="outline" onClick={exportTags}>
              <Download className="h-4 w-4 mr-2" />
              导出标签
            </Button>
            <Button variant="outline" onClick={importTags}>
              <Upload className="h-4 w-4 mr-2" />
              导入标签
            </Button>
            <Button 
              onClick={() => navigate('/tags/add')}
            >
              <Plus className="h-4 w-4 mr-2" />
              添加标签
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* 搜索区域 */}
          <div className="mb-4 flex items-center gap-2">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-8"
                placeholder="搜索标签名称..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch()
                  }
                }}
              />
            </div>
            <Button onClick={handleSearch} variant="outline">
              <Search className="h-4 w-4 mr-2" />
              搜索
            </Button>
            {searchText && (
              <Button 
                onClick={() => {
                  setSearchText('')
                  setPagination(prev => ({ ...prev, current: 1 }))
                }} 
                variant="ghost"
                size="sm"
              >
                清除
              </Button>
            )}
          </div>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedRowKeys.length === tags.length && tags.length > 0}
                      onCheckedChange={toggleAllSelection}
                    />
                  </TableHead>
                  <TableHead>标签名称</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>文章数量</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead className="w-[200px]">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                    </TableCell>
                  </TableRow>
                ) : tags.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                      暂无数据
                    </TableCell>
                  </TableRow>
                ) : (
                  tags.map((tag) => (
                    <TableRow key={tag.id}>
                      <TableCell>
                        <Checkbox
                          checked={selectedRowKeys.includes(tag.id)}
                          onCheckedChange={() => toggleRowSelection(tag.id)}
                        />
                      </TableCell>
                      <TableCell className="font-medium">{tag.name}</TableCell>
                      <TableCell>
                        <button
                          type="button"
                          onClick={() => handleToggleStatus(tag)}
                          disabled={statusUpdatingIds.includes(tag.id)}
                          className={cn(
                            'inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium transition-colors',
                            tag.status === 1
                              ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                              : tag.status === 0
                                ? 'bg-slate-200 text-slate-700 hover:bg-slate-300 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700'
                                : 'bg-red-600 text-white cursor-not-allowed'
                          )}
                          title={
                            tag.status === 2
                              ? t('tags.messages.statusBlockedDesc')
                              : tag.status === 1
                                ? t('tags.messages.clickToDisable')
                                : t('tags.messages.clickToEnable')
                          }
                        >
                          {statusUpdatingIds.includes(tag.id) ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : tag.status === 1 ? (
                            <CheckCircle2 className="h-3.5 w-3.5" />
                          ) : (
                            <Ban className="h-3.5 w-3.5" />
                          )}
                          {tag.status === 1
                            ? t('common.enabled')
                            : tag.status === 2
                              ? t('tags.statusBlocked')
                              : t('common.disabled')}
                        </button>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="font-mono">
                          {tag.article_count ?? 0}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDateTime(tag.created_at)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <a 
                            href={`/feed/tag/${tag.id}.rss`} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-primary hover:underline text-sm"
                          >
                            <Rss className="h-4 w-4" />
                          </a>
                          <Button variant="ghost" size="sm" onClick={() => navigate(`/tags/edit/${tag.id}`)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleDelete(tag.id)}>
                            <Trash2 className="h-4 w-4 text-destructive" />
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
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                共 {pagination.total} 条{searchText ? `（搜索: "${searchText}"）` : ''}，第 {pagination.current} / {totalPages} 页
              </div>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>跳转到</span>
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
                  <span>页</span>
                </div>
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
            <DialogDescription>确认删除该标签？</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>取消</Button>
            <Button variant="destructive" onClick={confirmDelete}>删除</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 批量删除确认对话框 */}
      <Dialog open={batchDeleteDialogOpen} onOpenChange={setBatchDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认批量删除</DialogTitle>
            <DialogDescription>确定要删除选中的 {selectedRowKeys.length} 个标签吗？</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBatchDeleteDialogOpen(false)}>取消</Button>
            <Button variant="destructive" onClick={confirmBatchDelete}>删除</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default TagList
