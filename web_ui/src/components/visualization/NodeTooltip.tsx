/**
 * 节点工具提示组件
 * 显示节点的详细信息和快捷操作
 */

import React, { useEffect, useRef} from 'react'
import {useNavigate} from 'react-router-dom'
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card'
import {Badge} from '@/components/ui/badge'
import {Button} from '@/components/ui/button'
import {ArrowRight, ExternalLink, Tag} from 'lucide-react'
import type {NodeTooltipProps} from '@/types/visualization'
import {cn} from '@/lib/utils'

export const NodeTooltip: React.FC<NodeTooltipProps> = ({
  node,
  position,
  visible,
  metadata,
  className = ''
}) => {
  const tooltipRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  // 调整位置避免超出视口
  const adjustPosition = () => {
    if (!tooltipRef.current || !node) return {x: position.x, y: position.y}

    const rect = tooltipRef.current.getBoundingClientRect()
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight

    let x = position.x
    let y = position.y

    // 调整水平位置
    if (x + rect.width > viewportWidth - 20) {
      x = viewportWidth - rect.width - 20
    }
    if (x < 20) {
      x = 20
    }

    // 调整垂直位置
    if (y + rect.height > viewportHeight - 20) {
      y = position.y - rect.height - 10
    }
    if (y < 20) {
      y = 20
    }

    return {x, y}
  }

  const adjustedPosition = adjustPosition()

  // 处理查看标签详情
  const handleViewDetails = () => {
    if (node) {
      navigate(`/tags/${node.id}`)
    }
  }

  // 处理查看聚类详情
  const handleViewCluster = () => {
    if (node && node.cluster) {
      navigate(`/tag-clusters/${node.cluster}`)
    }
  }

  if (!visible || !node) {
    return null
  }

  return (
    <div
      ref={tooltipRef}
      className={cn(
        'fixed z-50 w-80 transition-opacity duration-200',
        visible ? 'opacity-100' : 'opacity-0',
        className
      )}
      style={{
        left: `${adjustedPosition.x}px`,
        top: `${adjustedPosition.y}px`,
        pointerEvents: visible ? 'auto' : 'none'
      }}
    >
      <Card className="shadow-lg border-2">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <Tag className="h-5 w-5 text-primary flex-shrink-0" />
              <CardTitle className="text-base truncate">
                {node.name || node.id}
              </CardTitle>
            </div>
          </div>
          {node.cluster && metadata?.cluster_name && (
            <CardDescription className="text-xs mt-1">
              聚类: {metadata.cluster_name}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent className="space-y-3">
          {/* 基本信息 */}
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">标签ID:</span>
              <span className="font-mono text-xs bg-muted px-2 py-1 rounded">
                {node.id}
              </span>
            </div>

            {node.score !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">得分:</span>
                <Badge variant="secondary">
                  {(node.score * 100).toFixed(1)}%
                </Badge>
              </div>
            )}

            {node.size !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">大小:</span>
                <span className="font-medium">{node.size.toFixed(1)}</span>
              </div>
            )}

            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">坐标:</span>
              <span className="font-mono text-xs">
                ({node.x.toFixed(3)}, {node.y.toFixed(3)})
              </span>
            </div>
          </div>

          {/* 聚类信息 */}
          {metadata && (
            <div className="pt-2 border-t">
              <div className="text-xs text-muted-foreground mb-2">聚类信息</div>
              <div className="space-y-1 text-sm">
                {metadata.cluster_name && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">名称:</span>
                    <span className="font-medium">{metadata.cluster_name}</span>
                  </div>
                )}
                {metadata.centroid_tag_id && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">中心:</span>
                    <span className="font-mono text-xs">
                      {metadata.centroid_tag_id === node.id ? (
                        <Badge variant="default" className="text-xs">当前标签</Badge>
                      ) : (
                        metadata.centroid_tag_id
                      )}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 快捷操作 */}
          <div className="flex gap-2 pt-2">
            <Button
              size="sm"
              variant="outline"
              className="flex-1"
              onClick={handleViewDetails}
            >
              <ExternalLink className="h-3 w-3 mr-1" />
              详情
            </Button>
            {node.cluster && (
              <Button
                size="sm"
                variant="outline"
                className="flex-1"
                onClick={handleViewCluster}
              >
                <ArrowRight className="h-3 w-3 mr-1" />
                聚类
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default NodeTooltip