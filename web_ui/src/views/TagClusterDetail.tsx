import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useToast } from '@/hooks/use-toast'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { exportTagCluster, getTagCluster } from '@/api/tagClusters'
import { getClusterVisualization, getClusterNetwork } from '@/api/visualization'
import { EmbeddingScatterPlot, TagNetworkGraph, VisualizationControls } from '@/components/visualization'
import type {
  TagClusterDetail as TagClusterDetailType,
  TagClusterMergeSuggestion
} from '@/types/tagCluster'
import type { VisualizationConfig, VisualizationData } from '@/types/visualization'
import { ArrowLeft, Download, Loader2, Tags, Users, Activity } from 'lucide-react'
import { useTranslation } from 'react-i18next'

const formatScore = (value: number) => (value / 10000).toFixed(2)

const TagClusterDetail: React.FC = () => {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [cluster, setCluster] = useState<TagClusterDetailType | null>(null)
  const [clusterNotFound, setClusterNotFound] = useState(false)
  const [exporting, setExporting] = useState(false)

  const [vizConfig, setVizConfig] = useState<VisualizationConfig>({
    method: 'pca',
    includeEdges: true,
    minEdgeWeight: 0.5,
    normalize: true
  })
  const [networkMinSimilarity, setNetworkMinSimilarity] = useState(0.5)
  const [vizData, setVizData] = useState<VisualizationData | null>(null)
  const [vizLoading, setVizLoading] = useState(false)
  const [networkData, setNetworkData] = useState<VisualizationData | null>(null)
  const [networkLoading, setNetworkLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'scatter' | 'network'>('overview')

  const loadCluster = async () => {
    if (!id) return
    setLoading(true)
    setClusterNotFound(false)
    try {
      const res = await getTagCluster(id) as unknown as TagClusterDetailType
      setCluster(res)
    } catch (error: any) {
      if (error?.response?.status === 404) {
        setCluster(null)
        setClusterNotFound(true)
        return
      }
      toast({
        variant: 'destructive',
        title: t('common.error'),
        description: error?.response?.data?.message || error?.message || t('tagClusters.detail.messages.fetchFailed'),
      })
    } finally {
      setLoading(false)
    }
  }

  const loadVisualization = async () => {
    if (!id || clusterNotFound) return
    setVizLoading(true)
    try {
      const res = await getClusterVisualization(id, vizConfig) as unknown as VisualizationData
      setVizData(res)
    } catch (error: any) {
      if (error?.response?.status === 404) {
        setVizData(null)
        return
      }
      toast({
        variant: 'destructive',
        title: t('tagClusters.detail.visualization.loadFailed'),
        description: error?.response?.data?.message || error?.message || t('tagClusters.detail.visualization.getDataFailed'),
      })
    } finally {
      setVizLoading(false)
    }
  }

  const loadNetwork = async () => {
    if (!id || clusterNotFound) return
    setNetworkLoading(true)
    try {
      const res = await getClusterNetwork(id, {
        minSimilarity: networkMinSimilarity,
        maxNodes: 100
      }) as unknown as VisualizationData
      setNetworkData(res)
    } catch (error: any) {
      if (error?.response?.status === 404) {
        setNetworkData(null)
        return
      }
      toast({
        variant: 'destructive',
        title: t('tagClusters.detail.visualization.loadNetworkFailed'),
        description: error?.response?.data?.message || error?.message || t('tagClusters.detail.visualization.getNetworkFailed'),
      })
    } finally {
      setNetworkLoading(false)
    }
  }

  const handleExport = async () => {
    if (!id) return
    setExporting(true)
    try {
      const blob = await exportTagCluster(id) as unknown as Blob
      const url = window.URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = `tag-cluster-${id}.json`
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      window.URL.revokeObjectURL(url)
      toast({
        title: t('tagClusters.detail.exportSuccess'),
        description: t('tagClusters.detail.exportSuccessDesc'),
      })
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: t('tagClusters.detail.exportFailed'),
        description: error?.response?.data?.message || error?.message || t('tagClusters.detail.messages.exportFailed'),
      })
    } finally {
      setExporting(false)
    }
  }

  useEffect(() => {
    loadCluster()
  }, [id])

  useEffect(() => {
    if (cluster && activeTab === 'scatter') {
      loadVisualization()
    }
  }, [cluster, activeTab, vizConfig.method, vizConfig.includeEdges, vizConfig.minEdgeWeight, vizConfig.normalize])

  useEffect(() => {
    if (cluster && activeTab === 'network') {
      loadNetwork()
    }
  }, [cluster, activeTab, networkMinSimilarity])

  return (
    <div className="p-6 space-y-6">
      {clusterNotFound ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center gap-4 py-16">
            <div className="text-center">
              <h2 className="text-2xl font-semibold">{t('tagClusters.detail.notFoundTitle')}</h2>
              <p className="mt-2 text-sm text-muted-foreground">{t('tagClusters.detail.notFoundDesc')}</p>
            </div>
            <Button onClick={() => navigate('/tag-clusters')}>
              {t('tagClusters.detail.backToList')}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="flex items-center justify-between gap-4">
            <div>
              <Button variant="ghost" onClick={() => navigate(-1)} className="mb-3">
                <ArrowLeft className="mr-2 h-4 w-4" />
                {t('tagClusters.detail.back')}
              </Button>
              <div className="flex items-center gap-2">
                <h1 className="text-3xl font-bold">{t('tagClusters.detail.title')}</h1>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                {t('tagClusters.detail.subtitle')}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={handleExport} disabled={loading || exporting}>
                {exporting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
                {t('tagClusters.detail.exportJson')}
              </Button>
            </div>
          </div>

          <div className="flex gap-2 border-b">
            <Button
              variant={activeTab === 'overview' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('overview')}
              className="rounded-b-none"
            >
              <Users className="mr-2 h-4 w-4" />
              {t('tagClusters.detail.tabs.overview')}
            </Button>
            <Button
              variant={activeTab === 'scatter' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('scatter')}
              className="rounded-b-none"
            >
              <Activity className="mr-2 h-4 w-4" />
              {t('tagClusters.detail.tabs.scatter')}
            </Button>
            <Button
              variant={activeTab === 'network' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('network')}
              className="rounded-b-none"
            >
              <Tags className="mr-2 h-4 w-4" />
              {t('tagClusters.detail.tabs.network')}
            </Button>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>{t('tagClusters.detail.overview.clusterName')}</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <div className="text-xl font-semibold">{cluster?.name || '-'}</div>}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>{t('tagClusters.detail.overview.memberCount')}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2 text-xl font-semibold">
                  <Users className="h-5 w-5" />
                  {cluster?.size ?? 0}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>{t('tagClusters.detail.overview.centroidTag')}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap items-center gap-2">
                  <Tags className="h-5 w-5" />
                  <Badge variant="secondary">{cluster?.centroid_tag_name || cluster?.name || '-'}</Badge>
                  {cluster?.centroid_tag_id && (
                    <span className="text-xs text-muted-foreground">{cluster.centroid_tag_id}</span>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>{t('tagClusters.detail.overview.clusterInfo')}</CardTitle>
              <CardDescription>{cluster?.description || t('tagClusters.detail.overview.noDescription')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <div>{t('tagClusters.detail.overview.version')}：{cluster?.cluster_version || '-'}</div>
              <div>{t('tagClusters.detail.overview.clusterId')}：{cluster?.id || '-'}</div>
              <div>{t('tagClusters.detail.overview.updateTime')}：{cluster?.updated_at || '-'}</div>
            </CardContent>
          </Card>

          {activeTab === 'scatter' && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
              <div className="lg:col-span-1">
                <VisualizationControls
                  config={vizConfig}
                  onConfigChange={setVizConfig}
                  methods={['pca', 'tsne', 'umap']}
                  disabled={vizLoading}
                />
              </div>
              <div className="lg:col-span-3">
                {vizLoading ? (
                  <Card>
                    <CardContent className="flex items-center justify-center py-12">
                      <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    </CardContent>
                  </Card>
                ) : (
                  <EmbeddingScatterPlot
                    data={vizData || {nodes: [], edges: [], metadata: {method: vizConfig.method, node_count: 0, edge_count: 0}}}
                    height={500}
                    interactive={true}
                    onNodeClick={(node) => {
                      toast({
                        title: t('tagClusters.detail.visualization.nodeClick'),
                        description: `${t('tagClusters.detail.visualization.selectedTag')}: ${node.name || node.id}`,
                      })
                    }}
                  />
                )}
              </div>
            </div>
          )}

          {activeTab === 'network' && (
            <div className="grid grid-cols-1 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>{t('tagClusters.detail.network.title')}</CardTitle>
                  <CardDescription>{t('tagClusters.detail.network.description')}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="max-w-xs space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>{t('tagClusters.detail.network.threshold')}</span>
                      <Badge variant="secondary">{Math.round(networkMinSimilarity * 100)}%</Badge>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      step={5}
                      value={Math.round(networkMinSimilarity * 100)}
                      onChange={(event) => setNetworkMinSimilarity(Number(event.target.value) / 100)}
                      className="w-full"
                    />
                  </div>
                </CardContent>
              </Card>
              {networkLoading ? (
                <Card>
                  <CardContent className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  </CardContent>
                </Card>
              ) : (
                <TagNetworkGraph
                  data={networkData || {nodes: [], edges: [], metadata: {method: 'cooccurrence', node_count: 0, edge_count: 0}}}
                  height={600}
                  interactive={true}
                  showLabels={true}
                  onNodeClick={(node) => {
                    toast({
                      title: t('tagClusters.detail.visualization.nodeClick'),
                      description: `${t('tagClusters.detail.visualization.selectedTag')}: ${node.name || node.id}`,
                    })
                  }}
                />
              )}
            </div>
          )}

          {activeTab === 'overview' && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>{t('tagClusters.detail.overview.memberTags')}</CardTitle>
                  <CardDescription>{t('tagClusters.detail.overview.memberTagsDesc')}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>{t('tagClusters.detail.overview.tagName')}</TableHead>
                          <TableHead>{t('tagClusters.detail.overview.tagId')}</TableHead>
                          <TableHead>{t('tagClusters.detail.overview.memberScore')}</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {(cluster?.members || []).length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={3} className="h-20 text-center text-muted-foreground">
                              {loading ? t('common.loading') : t('tagClusters.detail.overview.noMembers')}
                            </TableCell>
                          </TableRow>
                        ) : (
                          cluster!.members.map((member) => (
                            <TableRow key={member.tag_id}>
                              <TableCell className="font-medium">{member.tag_name}</TableCell>
                              <TableCell className="text-muted-foreground">{member.tag_id}</TableCell>
                              <TableCell>
                                <Badge>{formatScore(member.member_score)}</Badge>
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>{t('tagClusters.detail.overview.mergeSuggestions')}</CardTitle>
                  <CardDescription>{t('tagClusters.detail.overview.mergeSuggestionsDesc')}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>{t('tagClusters.detail.overview.sourceTag')}</TableHead>
                          <TableHead>{t('tagClusters.detail.overview.candidateTarget')}</TableHead>
                          <TableHead>{t('tagClusters.detail.overview.totalScore')}</TableHead>
                          <TableHead>{t('tagClusters.detail.overview.reason')}</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {((cluster?.merge_suggestions || []) as TagClusterMergeSuggestion[]).length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={4} className="h-20 text-center text-muted-foreground">
                              {t('tagClusters.detail.overview.noMergeSuggestions')}
                            </TableCell>
                          </TableRow>
                        ) : (
                          cluster!.merge_suggestions!.map((item) => (
                            <TableRow key={`${item.source_tag_id}-${item.target_tag_id}`}>
                              <TableCell className="font-medium">{item.source_tag_name}</TableCell>
                              <TableCell>{item.target_tag_name}</TableCell>
                              <TableCell><Badge>{formatScore(item.score)}</Badge></TableCell>
                              <TableCell className="text-muted-foreground">{item.reason}</TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </>
      )}
    </div>
  )
}

export default TagClusterDetail
