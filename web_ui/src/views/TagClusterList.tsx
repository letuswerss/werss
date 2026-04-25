import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useToast } from '@/hooks/use-toast'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { rebuildTagClusters, listTagClusters } from '@/api/tagClusters'
import type { TagClusterListItem } from '@/types/tagCluster'
import { ArrowRight, Layers3, Loader2, RefreshCw, Search } from 'lucide-react'
import { useTranslation } from 'react-i18next'

const TagClusterList: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [rebuilding, setRebuilding] = useState(false)
  const [rebuildStartedAt, setRebuildStartedAt] = useState<number | null>(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [clusters, setClusters] = useState<TagClusterListItem[]>([])
  const [searchText, setSearchText] = useState('')
  const [page, setPage] = useState({ offset: 0, limit: 20, total: 0 })
  const [jumpPageInput, setJumpPageInput] = useState('1')

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

  const filteredClusters = useMemo(() => {
    if (!searchText.trim()) return clusters
    const keyword = searchText.trim().toLowerCase()
    return clusters.filter((item) =>
      (item.name || '').toLowerCase().includes(keyword) ||
      (item.description || '').toLowerCase().includes(keyword) ||
      (item.centroid_tag_id || '').toLowerCase().includes(keyword)
    )
  }, [clusters, searchText])

  const loadClusters = async () => {
    setLoading(true)
    try {
      const res = await listTagClusters({
        offset: 0,
        limit: 1000,
      }) as unknown as { list?: TagClusterListItem[]; page?: { total?: number } }
      const list = res.list || []
      setClusters(list)
      setPage((prev) => ({
        ...prev,
        total: res.page?.total || list.length,
        offset: 0,
      }))
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: t('common.error'),
        description: error?.message || t('tagClusters.messages.fetchFailed'),
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadClusters()
  }, [])

  useEffect(() => {
    setPage((prev) => ({ ...prev, offset: 0 }))
  }, [searchText])

  const rebuild = async () => {
    setRebuilding(true)
    setRebuildStartedAt(Date.now())
    try {
      const res = await rebuildTagClusters() as any
      toast({
        title: t('tagClusters.rebuildSuccess'),
        description: res?.data?.message || t('tagClusters.messages.rebuildSuccessDesc'),
      })
      await loadClusters()
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: t('tagClusters.rebuildFailed'),
        description: error?.response?.data?.message || error?.message || t('tagClusters.messages.rebuildFailed'),
      })
    } finally {
      setRebuilding(false)
      setRebuildStartedAt(null)
    }
  }

  const elapsedMinutes = Math.floor(elapsedSeconds / 60)
  const elapsedRemainingSeconds = elapsedSeconds % 60
  const elapsedText = `${String(elapsedMinutes).padStart(2, '0')}:${String(elapsedRemainingSeconds).padStart(2, '0')}`

  const totalPages = Math.max(1, Math.ceil(filteredClusters.length / page.limit))
  const currentPage = Math.floor(page.offset / page.limit) + 1
  const paginatedClusters = filteredClusters.slice(page.offset, page.offset + page.limit)

  useEffect(() => {
    setJumpPageInput(String(currentPage))
  }, [currentPage])

  const handleJumpPage = () => {
    const targetPage = Number.parseInt(jumpPageInput, 10)
    if (Number.isNaN(targetPage)) {
      setJumpPageInput(String(currentPage))
      return
    }

    const nextPage = Math.min(Math.max(targetPage, 1), totalPages)
    setPage((prev) => ({ ...prev, offset: (nextPage - 1) * prev.limit }))
    setJumpPageInput(String(nextPage))
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
              {t('tagClusters.rebuildModal.title')}
            </DialogTitle>
            <DialogDescription className="pt-1">
              {t('tagClusters.rebuildModal.description')}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="rounded-lg border bg-muted/30 p-4">
              <div className="flex items-center justify-between gap-4">
                <span className="text-sm font-medium">{t('tagClusters.rebuildModal.elapsed')}</span>
                <span className="font-mono text-lg font-semibold">{elapsedText}</span>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-muted">
                <div className="h-full w-1/3 animate-pulse rounded-full bg-primary" />
              </div>
            </div>

            <div className="space-y-2 text-sm text-muted-foreground">
              <p>{t('tagClusters.rebuildModal.noRealProgress')}</p>
              <p>{t('tagClusters.rebuildModal.hint')}</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold">{t('tagClusters.listTitle')}</h1>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">
            {t('tagClusters.listSubtitle')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={loadClusters} disabled={loading || rebuilding}>
            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
            {t('common.refresh')}
          </Button>
          <Button onClick={rebuild} disabled={loading || rebuilding}>
            {rebuilding ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
            {t('tagClusters.rebuild')}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('tagClusters.filter')}</CardTitle>
          <CardDescription>{t('tagClusters.filterDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <Input
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder={t('tagClusters.searchPlaceholder')}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('tagClusters.clusterList')}</CardTitle>
          <CardDescription>
            {t('tagClusters.totalDescription', { total: page.total, filtered: filteredClusters.length, current: paginatedClusters.length })}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('tagClusters.columns.name')}</TableHead>
                  <TableHead>{t('tagClusters.columns.description')}</TableHead>
                  <TableHead>{t('tagClusters.columns.centroidTag')}</TableHead>
                  <TableHead>{t('tagClusters.columns.memberCount')}</TableHead>
                  <TableHead>{t('tagClusters.columns.version')}</TableHead>
                  <TableHead className="text-right">{t('tagClusters.columns.actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedClusters.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                      {loading ? t('common.loading') : t('tagClusters.noData')}
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedClusters.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">{item.name}</TableCell>
                      <TableCell className="max-w-[360px] truncate text-muted-foreground">
                        {item.description || '-'}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{item.centroid_tag_id || '-'}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge>{item.size}</Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{item.cluster_version}</TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" onClick={() => navigate(`/tag-clusters/${item.id}`)}>
                          {t('tagClusters.view')}
                          <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          <div className="mt-4 flex items-center justify-between gap-4">
            <div className="text-sm text-muted-foreground">
              {t('common.page', { current: currentPage, total: totalPages, count: filteredClusters.length })}
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
                disabled={page.offset <= 0}
                onClick={() => setPage((prev) => ({ ...prev, offset: Math.max(0, prev.offset - prev.limit) }))}
              >
                {t('common.previousPage')}
              </Button>
              <Button
                variant="outline"
                disabled={page.offset + page.limit >= filteredClusters.length}
                onClick={() => setPage((prev) => ({ ...prev, offset: prev.offset + prev.limit }))}
              >
                {t('common.nextPage')}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default TagClusterList
