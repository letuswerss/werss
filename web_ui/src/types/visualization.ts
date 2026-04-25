/**
 * 可视化相关类型定义
 */

/**
 * 可视化节点
 */
export interface VisualizationNode {
  id: string
  name: string
  x: number
  y: number
  cluster: string
  score?: number
  size?: number
  [key: string]: any
}

/**
 * 可视化边
 */
export interface VisualizationEdge {
  source: string
  target: string
  weight: number
  embedding_score?: number
  cooccurrence_score?: number
  lexical_score?: number
  [key: string]: any
}

/**
 * 可视化数据
 */
export interface VisualizationData {
  nodes: VisualizationNode[]
  edges: VisualizationEdge[]
  metadata: VisualizationMetadata
}

/**
 * 可视化元数据
 */
export interface VisualizationMetadata {
  cluster_id?: string
  cluster_name?: string
  cluster_description?: string
  centroid_tag_id?: string
  cluster_size?: number
  method: string
  layout_type?: string
  node_count: number
  edge_count: number
  dimensions?: number
  min_similarity?: number
  min_cooccurrence_strength?: number
  warning?: string
  [key: string]: any
}

/**
 * 降维方法类型
 */
export type ReductionMethod = 'pca' | 'tsne' | 'umap'

/**
 * 布局类型
 */
export type LayoutType = 'force' | 'circular' | 'hierarchical'

/**
 * 可视化配置
 */
export interface VisualizationConfig {
  method: ReductionMethod
  layout?: LayoutType
  includeEdges?: boolean
  minEdgeWeight?: number
  normalize?: boolean
  maxNodes?: number
}

/**
 * 散点图属性
 */
export interface ScatterPlotProps {
  data: VisualizationData
  width?: string | number
  height?: number
  interactive?: boolean
  showTooltip?: boolean
  onNodeClick?: (node: VisualizationNode) => void
  onNodeHover?: (node: VisualizationNode | null) => void
  className?: string
}

/**
 * 网络图属性
 */
export interface NetworkGraphProps {
  data: VisualizationData
  width?: string | number
  height?: number
  layout?: LayoutType
  interactive?: boolean
  showLabels?: boolean
  onNodeClick?: (node: VisualizationNode) => void
  onNodeHover?: (node: VisualizationNode | null) => void
  className?: string
}

/**
 * 控制面板属性
 */
export interface VisualizationControlsProps {
  config: VisualizationConfig
  onConfigChange: (config: VisualizationConfig) => void
  methods?: ReductionMethod[]
  layouts?: LayoutType[]
  disabled?: boolean
  className?: string
}

/**
 * 工具提示属性
 */
export interface NodeTooltipProps {
  node: VisualizationNode | null
  position: { x: number; y: number }
  visible: boolean
  metadata?: VisualizationMetadata
  className?: string
}

/**
 * 可视化过滤器
 */
export interface VisualizationFilter {
  minScore?: number
  maxScore?: number
  clusterIds?: string[]
  tagIds?: string[]
  searchQuery?: string
}

/**
 * 可视化统计数据
 */
export interface VisualizationStats {
  totalNodes: number
  totalEdges: number
  avgDegree: number
  maxDegree: number
  clusters: number
  density: number
}
