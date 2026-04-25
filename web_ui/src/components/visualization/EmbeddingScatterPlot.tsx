/**
 * Embedding散点图组件
 * 使用VChart展示标签在2D空间中的分布
 */

import React, {Suspense, useRef, useState} from 'react'
import {useTheme} from '@/store'
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card'
import {Button} from '@/components/ui/button'
import {Badge} from '@/components/ui/badge'
import {Loader2, Download, RefreshCw} from 'lucide-react'
import type {VisualizationData, ScatterPlotProps, VisualizationNode} from '@/types/visualization'

// 懒加载VChart组件
const VChart = React.lazy(() =>
  import('@visactor/react-vchart').then(module => ({default: module.VChart}))
)

export const EmbeddingScatterPlot: React.FC<ScatterPlotProps> = ({
  data,
  width = '100%',
  height = 400,
  interactive = true,
  showTooltip = true,
  onNodeClick,
  onNodeHover,
  className = ''
}) => {
  const {theme} = useTheme()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [hoveredNode, setHoveredNode] = useState<any>(null)
  const chartRef = useRef<any>(null)

  const extractNodeFromEvent = (event: any): VisualizationNode | null => {
    const raw = event?.datum ?? event?.data?.datum ?? event?.data ?? null
    return raw && typeof raw === 'object' ? raw : null
  }

  // 生成VChart配置
  const generateSpec = () => {
    if (!data?.nodes || data.nodes.length === 0) {
      return null
    }

    const isDark = theme === 'dark'
    const primaryColor = isDark ? '#60a5fa' : '#3b82f6'
    const textColor = isDark ? '#e5e7eb' : '#374151'
    const gridColor = isDark ? '#374151' : '#e5e7eb'

    const plotData = data.nodes
      .filter(node => Number.isFinite(node.x) && Number.isFinite(node.y))
      .map(node => ({
      ...node,
      _x: node.x,
      _y: node.y,
      _name: node.name || node.id,
      _size: node.size || (node.score ? 5 + node.score * 15 : 8),
      _cluster: node.cluster || data.metadata.cluster_name || 'default'
    }))

    if (plotData.length === 0) {
      return null
    }

    return {
      type: 'scatter',
      background: 'transparent',
      data: {
        values: plotData
      },
      xField: '_x',
      yField: '_y',
      seriesField: '_cluster',
      sizeField: '_size',
      size: {
        type: 'linear',
        range: [8, 20]
      },
      point: {
        visible: true,
        style: {
          fillOpacity: interactive ? 0.7 : 0.6,
          stroke: primaryColor,
          strokeWidth: 1.5
        }
      },
      axes: [
        {
          orient: 'bottom',
          type: 'linear',
          visible: false,
          grid: {
            visible: false,
            style: {
              stroke: gridColor
            }
          }
        },
        {
          orient: 'left',
          type: 'linear',
          visible: false,
          grid: {
            visible: false,
            style: {
              stroke: gridColor
            }
          }
        }
      ],
      legends: {
        visible: false
      },
      tooltip: {
        visible: showTooltip,
        trigger: 'hover',
        renderMode: 'html',
        mark: {
          content: [
            { key: () => '标签', value: (datum: any) => datum?._name || datum?.id || '-' },
            { key: () => 'ID', value: (datum: any) => datum?.id || '-' },
            {
              key: () => '得分',
              value: (datum: any) => (
                typeof datum?.score === 'number' ? `${(datum.score * 100).toFixed(1)}%` : '-'
              )
            },
            {
              key: () => '位置',
              value: (datum: any) => {
                const x = typeof datum?._x === 'number' ? datum._x.toFixed(2) : '-'
                const y = typeof datum?._y === 'number' ? datum._y.toFixed(2) : '-'
                return `(${x}, ${y})`
              }
            }
          ]
        }
      },
      animation: true,
      animationAppear: {
        duration: 600
      }
    }
  }

  const spec = generateSpec()

  // 处理图表点击事件
  const handleChartClick = (datum: any) => {
    const nodeData = extractNodeFromEvent(datum)
    if (nodeData) {
      setSelectedNode(nodeData)
      if (onNodeClick) {
        onNodeClick(nodeData)
      }
    }
  }

  // 处理图表悬停事件
  const handleChartHover = (datum: any) => {
    const nodeData = extractNodeFromEvent(datum)
    if (nodeData) {
      setHoveredNode(nodeData)
      if (onNodeHover) {
        onNodeHover(nodeData)
      }
    } else {
      setHoveredNode(null)
      if (onNodeHover) {
        onNodeHover(null)
      }
    }
  }

  // 刷新图表
  const handleRefresh = () => {
    setLoading(true)
    setError(null)
    // 模拟刷新延迟
    setTimeout(() => {
      setLoading(false)
    }, 500)
  }

  // 下载图表
  const handleDownload = () => {
    if (chartRef.current) {
      // 这里可以实现图表下载功能
      const link = document.createElement('a')
      link.download = `scatter-plot-${Date.now()}.png`
      link.href = '' // 需要实际的图表截图实现
      link.click()
    }
  }

  if (!spec) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center text-muted-foreground">
            <p>暂无可视化数据</p>
            {data?.metadata?.warning && (
              <p className="text-sm mt-2 text-orange-500">{data.metadata.warning}</p>
            )}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>聚类可视化</CardTitle>
            <CardDescription>
              标签在向量空间中的分布 ({data.metadata.method?.toUpperCase()}降维)
              {data.metadata.dimensions && ` - ${data.metadata.dimensions}维→2维`}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="text-center text-red-500 py-8">
            <p>加载失败: {error}</p>
            <Button variant="outline" size="sm" onClick={handleRefresh} className="mt-4">
              重试
            </Button>
          </div>
        ) : (
          <Suspense fallback={<div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>}>
            <div style={{width, height}} className="mx-auto">
              <VChart
                ref={chartRef}
                spec={spec}
                onClick={handleChartClick}
                onMouseOver={handleChartHover}
                onMouseLeave={() => handleChartHover(null)}
                style={{width: '100%', height: '100%'}}
              />
            </div>
          </Suspense>
        )}

        {/* 统计信息 */}
        <div className="mt-4 flex items-center gap-4 text-sm text-muted-foreground">
          <Badge variant="secondary">{data.metadata.node_count} 个节点</Badge>
          {data.metadata.edge_count > 0 && (
            <Badge variant="secondary">{data.metadata.edge_count} 条边</Badge>
          )}
          {selectedNode && (
            <div className="ml-auto text-right">
              <span className="font-medium text-foreground">选中: </span>
              {selectedNode.name || selectedNode.id}
            </div>
          )}
        </div>

        {/* 说明信息 */}
        {data.metadata.warning && (
          <div className="mt-4 p-3 bg-orange-50 dark:bg-orange-900/20 rounded border border-orange-200 dark:border-orange-800">
            <p className="text-sm text-orange-600 dark:text-orange-400">
              ⚠️ {data.metadata.warning}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default EmbeddingScatterPlot
