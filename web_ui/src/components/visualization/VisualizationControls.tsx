/**
 * 可视化控制面板组件
 * 提供降维方法、布局算法、过滤等控制选项
 */

import React from 'react'
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card'
import {Label} from '@/components/ui/label'
import {Button} from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {Switch} from '@/components/ui/switch'
import {Settings, RefreshCw} from 'lucide-react'
import type {VisualizationControlsProps, ReductionMethod, LayoutType} from '@/types/visualization'
import {cn} from '@/lib/utils'

export const VisualizationControls: React.FC<VisualizationControlsProps> = ({
  config,
  onConfigChange,
  methods = ['pca', 'tsne', 'umap'],
  layouts = ['force', 'circular', 'hierarchical'],
  disabled = false,
  className = ''
}) => {
  // 降维方法说明
  const methodDescriptions: Record<ReductionMethod, string> = {
    pca: 'PCA - 快速稳定，保持全局结构',
    tsne: 't-SNE - 高质量但较慢，保持局部结构',
    umap: 'UMAP - 平衡性能和质量，保持局部和全局结构'
  }

  // 布局类型说明
  const layoutDescriptions: Record<LayoutType, string> = {
    force: '力导向 - 物理模拟，自然分布',
    circular: '环形布局 - 节点沿圆周排列',
    hierarchical: '层级布局 - 树状结构展示'
  }

  // 处理配置变化
  const handleConfigChange = (updates: Partial<typeof config>) => {
    onConfigChange({...config, ...updates})
  }

  // 快速配置预设
  const presets = [
    {name: '快速预览', config: {method: 'pca' as ReductionMethod, includeEdges: false, normalize: true}},
    {name: '标准分析', config: {method: 'umap' as ReductionMethod, includeEdges: true, normalize: true}},
    {name: '高质量', config: {method: 'tsne' as ReductionMethod, includeEdges: true, normalize: true}},
    {name: '关系分析', config: {method: 'umap' as ReductionMethod, includeEdges: true, minEdgeWeight: 0.7, normalize: true}}
  ]

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Settings className="h-5 w-5 text-primary" />
          <CardTitle className="text-lg">可视化设置</CardTitle>
        </div>
        <CardDescription>调整可视化参数和显示选项</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 快速预设 */}
        <div className="space-y-3">
          <Label className="text-sm font-medium">快速预设</Label>
          <div className="flex flex-wrap gap-2">
            {presets.map((preset) => (
              <Button
                key={preset.name}
                variant="outline"
                size="sm"
                onClick={() => handleConfigChange(preset.config)}
                disabled={disabled}
                className="text-xs"
              >
                {preset.name}
              </Button>
            ))}
          </div>
        </div>

        {/* 降维方法选择 */}
        <div className="space-y-3">
          <Label htmlFor="method-select" className="text-sm font-medium">
            降维方法
          </Label>
          <Select
            value={config.method}
            onValueChange={(value: ReductionMethod) => handleConfigChange({method: value})}
            disabled={disabled}
          >
            <SelectTrigger id="method-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {methods.map((method) => (
                <SelectItem key={method} value={method}>
                  <div className="flex flex-col">
                    <span className="font-medium">{method.toUpperCase()}</span>
                    <span className="text-xs text-muted-foreground">
                      {methodDescriptions[method]}
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* 布局类型选择 */}
        {config.layout && (
          <div className="space-y-3">
            <Label htmlFor="layout-select" className="text-sm font-medium">
              布局算法
            </Label>
            <Select
              value={config.layout}
              onValueChange={(value: LayoutType) => handleConfigChange({layout: value})}
              disabled={disabled}
            >
              <SelectTrigger id="layout-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {layouts.map((layout) => (
                  <SelectItem key={layout} value={layout}>
                    <div className="flex flex-col">
                      <span className="font-medium">{layout}</span>
                      <span className="text-xs text-muted-foreground">
                        {layoutDescriptions[layout]}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* 显示选项 */}
        <div className="space-y-4">
          <Label className="text-sm font-medium">显示选项</Label>

          {/* 显示边 */}
          {config.includeEdges !== undefined && (
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="edges-toggle" className="text-sm">显示关系边</Label>
                <p className="text-xs text-muted-foreground">
                  显示标签间的相似度关系
                </p>
              </div>
              <Switch
                id="edges-toggle"
                checked={config.includeEdges}
                onCheckedChange={(checked) => handleConfigChange({includeEdges: checked})}
                disabled={disabled}
              />
            </div>
          )}

          {/* 归一化坐标 */}
          {config.normalize !== undefined && (
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="normalize-toggle" className="text-sm">归一化坐标</Label>
                <p className="text-xs text-muted-foreground">
                  将坐标缩放到统一范围
                </p>
              </div>
              <Switch
                id="normalize-toggle"
                checked={config.normalize}
                onCheckedChange={(checked) => handleConfigChange({normalize: checked})}
                disabled={disabled}
              />
            </div>
          )}
        </div>

        {/* 边权重阈值 */}
        {config.includeEdges && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="edge-weight-slider" className="text-sm font-medium">
                最小边权重
              </Label>
              <span className="text-sm text-muted-foreground">
                {config.minEdgeWeight ? (config.minEdgeWeight * 100).toFixed(0) : '50'}%
              </span>
            </div>
            <input
              id="edge-weight-slider"
              type="range"
              value={config.minEdgeWeight || 0.5}
              onChange={(e) => handleConfigChange({minEdgeWeight: parseFloat(e.target.value)})}
              min={0}
              max={1}
              step={0.05}
              disabled={disabled}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
            />
            <p className="text-xs text-muted-foreground">
              只显示相似度高于此阈值的关系
            </p>
          </div>
        )}

        {/* 节点数量限制 */}
        {config.maxNodes !== undefined && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="max-nodes-slider" className="text-sm font-medium">
                最大节点数
              </Label>
              <span className="text-sm text-muted-foreground">
                {config.maxNodes}
              </span>
            </div>
            <input
              id="max-nodes-slider"
              type="range"
              value={config.maxNodes}
              onChange={(e) => handleConfigChange({maxNodes: parseInt(e.target.value)})}
              min={10}
              max={500}
              step={10}
              disabled={disabled}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
            />
            <p className="text-xs text-muted-foreground">
              限制显示的节点数量以提高性能
            </p>
          </div>
        )}

        {/* 重置按钮 */}
        <div className="pt-4 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleConfigChange({
              method: 'pca',
              includeEdges: true,
              minEdgeWeight: 0.5,
              normalize: true
            })}
            disabled={disabled}
            className="w-full"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            重置为默认设置
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default VisualizationControls