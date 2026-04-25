import http from './http'

/**
 * 统计数据接口
 */
export interface DashboardStats {
  totalArticles: number
  totalSources: number
  todayArticles: number
  weekArticles: number
}

/**
 * 来源统计接口
 */
export interface SourceStats {
  mp_id: string
  mp_name: string
  article_count: number
  percentage: number
}

/**
 * 热词统计接口
 */
export interface KeywordStats {
  keyword: string
  count: number
}

/**
 * 关键词趋势数据接口
 */
export interface KeywordTrendData {
  date: string
  keywords: { [keyword: string]: number }
}

/**
 * 趋势数据接口（按公众号分组）
 */
export interface TrendData {
  date: string
  sources: { [mp_name: string]: number } // 每个公众号当天的文章数
}

/**
 * Dashboard 数据接口
 */
export interface DashboardData {
  stats: DashboardStats
  sourceStats: SourceStats[]
  keywordStats: KeywordStats[]
  trendData: TrendData[]
  keywordTrendData?: KeywordTrendData[]
}

/**
 * 获取 Dashboard 统计数据
 */
export const getDashboardStats = () => {
  return http.get<{ code: number; data: DashboardData }>('/wx/dashboard/stats')
}

