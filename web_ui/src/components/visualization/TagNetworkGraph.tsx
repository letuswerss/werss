import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useTheme } from '@/store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Download, Maximize2, ZoomIn, ZoomOut } from 'lucide-react'
import type { VisualizationData, NetworkGraphProps, VisualizationNode } from '@/types/visualization'

const VIEWBOX_WIDTH = 800
const VIEWBOX_HEIGHT = 600

const buildFallbackLayout = (nodes: VisualizationNode[]) => {
  const centerX = VIEWBOX_WIDTH / 2
  const centerY = VIEWBOX_HEIGHT / 2
  const radius = Math.min(VIEWBOX_WIDTH, VIEWBOX_HEIGHT) * 0.32
  return nodes.map((node, index) => {
    if (Number.isFinite(node.x) && Number.isFinite(node.y)) {
      return {
        ...node,
        fx: node.x,
        fy: node.y,
        radius: node.size || (node.score ? 5 + node.score * 15 : 8)
      }
    }
    const angle = (Math.PI * 2 * index) / Math.max(nodes.length, 1)
    return {
      ...node,
      fx: centerX + Math.cos(angle) * radius,
      fy: centerY + Math.sin(angle) * radius,
      radius: node.size || (node.score ? 5 + node.score * 15 : 8)
    }
  })
}

export const TagNetworkGraph: React.FC<NetworkGraphProps> = ({
  data,
  width = '100%',
  height = 500,
  interactive = true,
  showLabels = true,
  onNodeClick,
  onNodeHover,
  className = ''
}) => {
  const { t } = useTranslation()
  const { theme } = useTheme()
  const svgRef = useRef<SVGSVGElement>(null)
  const [zoom, setZoom] = useState(1)
  const [selectedNode, setSelectedNode] = useState<any>(null)

  const networkData = useMemo(() => {
    if (!data?.nodes || data.nodes.length === 0) {
      return null
    }
    return {
      nodes: buildFallbackLayout(data.nodes),
      edges: data.edges || []
    }
  }, [data])

  const renderNetwork = () => {
    if (!networkData || !svgRef.current) return

    const svg = svgRef.current
    const { nodes, edges } = networkData

    while (svg.firstChild) {
      svg.removeChild(svg.firstChild)
    }

    const isDark = theme === 'dark'
    const nodeColor = isDark ? '#60a5fa' : '#2563eb'
    const edgeColor = isDark ? '#4b5563' : '#cbd5e1'
    const textColor = isDark ? '#e5e7eb' : '#334155'

    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g')
    g.setAttribute('transform', `scale(${zoom})`)
    svg.appendChild(g)

    edges.forEach((edge) => {
      const sourceNode = nodes.find((node) => node.id === edge.source)
      const targetNode = nodes.find((node) => node.id === edge.target)
      if (!sourceNode || !targetNode) return

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
      line.setAttribute('x1', String(sourceNode.fx))
      line.setAttribute('y1', String(sourceNode.fy))
      line.setAttribute('x2', String(targetNode.fx))
      line.setAttribute('y2', String(targetNode.fy))
      line.setAttribute('stroke', edgeColor)
      line.setAttribute('stroke-width', String(Math.max(1, edge.weight * 3)))
      line.setAttribute('stroke-opacity', String(0.3 + edge.weight * 0.6))
      g.appendChild(line)
    })

    nodes.forEach((node) => {
      const group = document.createElementNS('http://www.w3.org/2000/svg', 'g')
      group.setAttribute('class', 'node-group')
      group.setAttribute('data-node-id', node.id)
      group.style.cursor = interactive ? 'pointer' : 'default'

      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle')
      circle.setAttribute('cx', String(node.fx))
      circle.setAttribute('cy', String(node.fy))
      circle.setAttribute('r', String(node.radius))
      circle.setAttribute('fill', nodeColor)
      circle.setAttribute('fill-opacity', '0.65')
      circle.setAttribute('stroke', nodeColor)
      circle.setAttribute('stroke-width', '2')
      group.appendChild(circle)

      if (showLabels) {
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text')
        text.setAttribute('x', String(node.fx + node.radius + 5))
        text.setAttribute('y', String(node.fy + 4))
        text.setAttribute('fill', textColor)
        text.setAttribute('font-size', '12')
        text.setAttribute('font-family', 'system-ui, sans-serif')
        text.textContent = node.name || node.id
        group.appendChild(text)
      }

      if (interactive) {
        group.addEventListener('click', () => {
          setSelectedNode(node)
          onNodeClick?.(node)
        })

        group.addEventListener('mouseenter', () => {
          circle.setAttribute('fill-opacity', '1')
          circle.setAttribute('stroke-width', '3')
          onNodeHover?.(node)
        })

        group.addEventListener('mouseleave', () => {
          circle.setAttribute('fill-opacity', '0.65')
          circle.setAttribute('stroke-width', '2')
          onNodeHover?.(null)
        })
      }

      g.appendChild(group)
    })
  }

  useEffect(() => {
    renderNetwork()
  }, [networkData, theme, zoom, showLabels])

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.2, 3))
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.2, 0.2))
  const handleResetZoom = () => setZoom(1)

  const handleDownload = () => {
    if (!svgRef.current) return
    const svgData = new XMLSerializer().serializeToString(svgRef.current)
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()

    img.onload = () => {
      canvas.width = img.width
      canvas.height = img.height
      ctx?.drawImage(img, 0, 0)
      const link = document.createElement('a')
      link.download = `network-graph-${Date.now()}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()
    }

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
  }

  if (!networkData) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center text-muted-foreground">
            <p>{t('tagClusters.detail.network.noData')}</p>
            {data?.metadata?.warning && (
              <p className="mt-2 text-sm text-orange-500">{data.metadata.warning}</p>
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
            <CardTitle>{t('tagClusters.detail.network.graphTitle')}</CardTitle>
            <CardDescription>{t('tagClusters.detail.network.graphDescription')}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex items-center justify-end gap-2">
          <Button variant="outline" size="sm" onClick={handleZoomOut} disabled={zoom <= 0.2}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={handleResetZoom}>
            {Math.round(zoom * 100)}%
          </Button>
          <Button variant="outline" size="sm" onClick={handleZoomIn} disabled={zoom >= 3}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={handleResetZoom}>
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>

        <div
          className="overflow-hidden rounded-lg border bg-background"
          style={{ width, height: typeof height === 'number' ? `${height}px` : height }}
        >
          <svg
            ref={svgRef}
            width="100%"
            height="100%"
            viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
            preserveAspectRatio="xMidYMid meet"
            style={{ background: theme === 'dark' ? '#111827' : '#ffffff' }}
          />
        </div>

        <div className="mt-4 flex items-center gap-4 text-sm text-muted-foreground">
          <Badge variant="secondary">{data.metadata.node_count} {t('tagClusters.detail.network.nodes')}</Badge>
          <Badge variant="secondary">{data.metadata.edge_count} {t('tagClusters.detail.network.edges')}</Badge>
          {typeof data.metadata.min_cooccurrence_strength === 'number' && (
            <Badge variant="secondary">
              {t('tagClusters.detail.network.thresholdBadge')}: {(data.metadata.min_cooccurrence_strength * 100).toFixed(0)}%
            </Badge>
          )}
          {selectedNode && (
            <div className="ml-auto text-right">
              <span className="font-medium text-foreground">{t('tagClusters.detail.network.selected')}: </span>
              {selectedNode.name || selectedNode.id}
            </div>
          )}
        </div>

        {data.metadata.warning && (
          <div className="mt-4 rounded border border-orange-200 bg-orange-50 p-3 dark:border-orange-800 dark:bg-orange-900/20">
            <p className="text-sm text-orange-600 dark:text-orange-400">{data.metadata.warning}</p>
          </div>
        )}

        <div className="mt-4 rounded border border-blue-200 bg-blue-50 p-3 dark:border-blue-800 dark:bg-blue-900/20">
          <p className="text-sm text-blue-600 dark:text-blue-400">
            {t('tagClusters.detail.network.hint')}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

export default TagNetworkGraph
