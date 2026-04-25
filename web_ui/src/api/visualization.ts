/**
 * 可视化相关API调用
 */

import http from './http'
import type {
  VisualizationData,
  VisualizationConfig,
  ReductionMethod,
  LayoutType
} from '@/types/visualization'

/**
 * 获取聚类可视化数据
 */
export const getClusterVisualization = (
  clusterId: string,
  config?: Partial<VisualizationConfig>
) => {
  const params = {
    method: config?.method || 'pca',
    include_edges: config?.includeEdges !== false,
    min_edge_weight: config?.minEdgeWeight || 0.5,
    normalize: config?.normalize !== false
  }

  return http.get<VisualizationData>(
    `/wx/tag-clusters/${clusterId}/visualization`,
    { params }
  )
}

/**
 * 获取聚类网络图数据
 */
export const getClusterNetwork = (
  clusterId: string,
  config?: {
    minSimilarity?: number
    layoutType?: LayoutType
    maxNodes?: number
  }
) => {
  const params = {
    min_similarity: config?.minSimilarity || 0.7,
    layout_type: config?.layoutType || 'force',
    max_nodes: config?.maxNodes || 100
  }

  return http.get<VisualizationData>(
    `/wx/tag-clusters/${clusterId}/network`,
    { params }
  )
}

/**
 * 获取聚类概览可视化数据
 */
export const getClustersOverview = (config?: {
  method?: ReductionMethod
  limit?: number
}) => {
  const params = {
    method: config?.method || 'pca',
    limit: config?.limit || 10
  }

  return http.get<VisualizationData>(
    '/wx/tag-clusters/overview/visualization',
    { params }
  )
}

/**
 * 下载可视化数据为JSON
 */
export const downloadVisualizationData = (data: VisualizationData, filename: string = 'visualization.json') => {
  const jsonStr = JSON.stringify(data, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 导出可视化图片 (需要图表库支持)
 */
export const exportVisualizationImage = async (
  elementId: string,
  filename: string = 'visualization.png'
) => {
  const element = document.getElementById(elementId)
  if (!element) {
    throw new Error('Element not found')
  }

  // 使用html2canvas或其他截图库
  // 这里提供基础实现，具体实现依赖于使用的图表库
  try {
    const html2canvas = (await import('html2canvas')).default
    const canvas = await html2canvas(element)
    canvas.toBlob((blob) => {
      if (blob) {
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      }
    })
  } catch (error) {
    console.error('Failed to export image:', error)
    throw new Error('Failed to export visualization as image')
  }
}