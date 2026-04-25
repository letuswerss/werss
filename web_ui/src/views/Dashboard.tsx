import React, { useState, useEffect, lazy, Suspense, ErrorInfo, Component } from 'react'
import { useTranslation } from 'react-i18next'
import { getDashboardStats, type DashboardData, type SourceStats, type KeywordStats, type TrendData, type KeywordTrendData } from '@/api/dashboard'
import { getArticles, type Article } from '@/api/article'
import { getSubscriptions, type Subscription } from '@/api/subscription'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Statistic } from '@/components/extensions/statistic'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { ButtonGroup } from '@/components/ui/button-group'
import { Loader2, FileText, User, Calendar, Flame } from 'lucide-react'
import { useTheme } from '@/store'

// --- 关键修改：动态导入 VChart ---
// 1. 将体积庞大的图表库与主包分离
// 2. 解决模块初始化顺序导致的 ReferenceError: Cannot access 'GE' before initialization
const VChart = lazy(() => 
  import('@visactor/react-vchart').then(module => ({ 
    default: module.VChart 
  })).catch(error => {
    console.error('VChart 加载失败:', error)
    // 返回一个占位组件
    return {
      default: ({ style }: any) => {
        // 这里不能直接使用 hook，使用默认文本
        return (
          <div style={style} className="flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <div className="mb-2">图表加载失败</div>
              <div className="text-sm">请刷新页面重试</div>
            </div>
          </div>
        )
      }
    } as any
  })
)

// 错误边界组件
class ChartErrorBoundary extends Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('图表渲染错误:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex items-center justify-center h-[400px] text-muted-foreground">
          <div className="text-center">
            <div className="mb-2">图表渲染失败</div>
            <div className="text-sm">请刷新页面重试</div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

const Dashboard: React.FC = () => {
  const { t } = useTranslation()
  const { theme } = useTheme()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  
  // 视图控制状态
  const [keywordDateRange, setKeywordDateRange] = useState<7 | 30>(30) // 时间范围：7天或30天
  const [keywordChartType, setKeywordChartType] = useState<'stack' | 'line'>('stack')

  // 检测当前实际主题
  const isDarkMode = () => {
    if (theme === 'dark') return true
    if (theme === 'light') return false
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ||
             document.documentElement.classList.contains('dark') ||
             document.documentElement.hasAttribute('data-theme')
    }
    return false
  }

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError('')
      
      try {
        const res = await getDashboardStats()
        if (res && (res as any).data) {
          const responseData = (res as any).data
          if (responseData.code === 0 || responseData.code === 200) {
            setDashboardData(responseData.data)
            return
          } else {
            const errorMsg = responseData.message || responseData.msg || '未知错误'
            console.error('Dashboard API 返回错误:', responseData.code, errorMsg)
            // 降级处理
            await calculateStatsFromAPIs()
            return
          }
        }
      } catch (apiError: any) {
        console.warn('Dashboard API 调用失败，使用回退计算:', apiError)
        await calculateStatsFromAPIs()
        return
      }
      
      await calculateStatsFromAPIs()
    } catch (err: any) {
      console.error('获取统计数据失败:', err)
      setError(t('dashboard.errors.fetchFailed', { message: err?.message || t('dashboard.errors.unknownError') }))
    } finally {
      setLoading(false)
    }
  }

  // --- 回退计算逻辑 (保持原有逻辑不变) ---
  const calculateStatsFromAPIs = async () => {
    try {
      const articlesRes = await getArticles({ page: 0, pageSize: 100 })
      const articles: Article[] = (articlesRes as any)?.list || (articlesRes as any)?.data?.list || []
      const totalArticles = (articlesRes as any)?.total || (articlesRes as any)?.data?.total || articles.length

      const subscriptionsRes = await getSubscriptions({ page: 0, pageSize: 100 })
      const subscriptions: Subscription[] = (subscriptionsRes as any)?.list || (subscriptionsRes as any)?.data?.list || []
      const totalSources = (subscriptionsRes as any)?.total || (subscriptionsRes as any)?.data?.total || subscriptions.length

      const now = new Date()
      const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      const weekStart = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      
      const todayArticles = articles.filter(article => new Date(article.created_at) >= todayStart).length
      const weekArticles = articles.filter(article => new Date(article.created_at) >= weekStart).length

      // 来源统计
      const sourceMap = new Map<string, { mp_id: string; mp_name: string; count: number }>()
      articles.forEach(article => {
        const key = article.mp_name || t('common.unknownError')
        const existing = sourceMap.get(key) || { mp_id: article.mp_name || '', mp_name: key, count: 0 }
        existing.count++
        sourceMap.set(key, existing)
      })
      
      const sourceStats: SourceStats[] = Array.from(sourceMap.values())
        .map(item => ({
          mp_id: item.mp_id,
          mp_name: item.mp_name,
          article_count: item.count,
          percentage: totalArticles > 0 ? (item.count / totalArticles) * 100 : 0
        }))
        .sort((a, b) => b.article_count - a.article_count)
        .slice(0, 10)

      // 关键词统计
      const keywordMap = new Map<string, number>()
      const keywordTrendMap = new Map<string, Map<string, number>>()
      const keywordTrendThirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      const invalidKeywordPattern = /^[a-z]{1,2}$|^[0-9]+$|^[^\u4e00-\u9fa5a-zA-Z0-9]+$|^\.+$/
      
      articles.forEach((article: any) => {
        let articleDate: Date
        let dateKey: string
        
        if (article.publish_time) {
          const publishTimestamp = typeof article.publish_time === 'number' ? article.publish_time : parseInt(article.publish_time)
          const timestampMs = publishTimestamp < 10000000000 ? publishTimestamp * 1000 : publishTimestamp
          articleDate = new Date(timestampMs)
        } else {
          articleDate = new Date(article.created_at)
        }
        dateKey = articleDate.toISOString().split('T')[0]
        
        const tags = article.tags || article.tag_names || []
        const keywords: string[] = []
        
        if (Array.isArray(tags)) {
          tags.forEach((tag: any) => {
            const keyword = typeof tag === 'string' ? tag : (tag?.name || tag?.tag_name || '')
            if (keyword && keyword.trim()) {
              const trimmedKeyword = keyword.trim()
              if (trimmedKeyword.length >= 2 && !invalidKeywordPattern.test(trimmedKeyword) && trimmedKeyword.length <= 20) {
                keywords.push(trimmedKeyword)
              }
            }
          })
        }
        
        keywords.forEach(keyword => {
          if (articleDate >= keywordTrendThirtyDaysAgo) {
            keywordMap.set(keyword, (keywordMap.get(keyword) || 0) + 1)
            if (!keywordTrendMap.has(dateKey)) {
              keywordTrendMap.set(dateKey, new Map())
            }
            keywordTrendMap.get(dateKey)!.set(keyword, (keywordTrendMap.get(dateKey)!.get(keyword) || 0) + 1)
          }
        })
      })

      // 基于所有数据生成关键词统计（用于标签视图）
      const keywordStats: KeywordStats[] = Array.from(keywordMap.entries())
        .map(([keyword, count]) => ({ keyword, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 20)
      
      // 生成所有可用的趋势数据（30天），后续根据选择的时间范围过滤
      const dateRange30: string[] = []
      for (let i = 29; i >= 0; i--) {
        dateRange30.push(new Date(now.getTime() - i * 24 * 60 * 60 * 1000).toISOString().split('T')[0])
      }
      
      // ⚠️ 关键修复：基于过去30天的趋势数据生成 topKeywords
      // 这样确保图表中显示的关键词在过去30天内确实有出现
      const trendKeywordMap = new Map<string, number>()
      keywordTrendMap.forEach((dayMap) => {
        dayMap.forEach((count, keyword) => {
          trendKeywordMap.set(keyword, (trendKeywordMap.get(keyword) || 0) + count)
        })
      })
      
      // 基于趋势数据生成热门关键词（只包含过去30天内出现的关键词）
      const trendKeywordStats = Array.from(trendKeywordMap.entries())
        .map(([keyword, count]) => ({ keyword, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10)
      
      let topKeywords = trendKeywordStats.map(k => k.keyword)
      let usingFallback = false
      
      // 如果过去30天没有关键词数据，使用全局统计的前10个作为备选
      if (topKeywords.length === 0 && keywordStats.length > 0) {
        console.warn('过去30天没有关键词数据，使用全局统计')
        const fallbackKeywords = keywordStats.slice(0, 10).map(k => k.keyword)
        topKeywords = fallbackKeywords
        usingFallback = true
      }
      
      // 生成完整的30天趋势数据
      const keywordTrendData30: KeywordTrendData[] = dateRange30.map(date => {
        const dayKeywords = keywordTrendMap.get(date) || new Map()
        const keywords: { [key: string]: number } = {}
        topKeywords.forEach(keyword => {
          keywords[keyword] = dayKeywords.get(keyword) || 0
        })
        return { date, keywords }
      })
      
      // 调试信息：检查数据是否正确生成
      if (keywordTrendData30.length > 0 && topKeywords.length > 0) {
        // 检查是否有实际数据
        const hasActualData = keywordTrendData30.some(item => 
          topKeywords.some(keyword => (item.keywords[keyword] || 0) > 0)
        )
        
        // 统计每个关键词的总出现次数
        const keywordTotals: { [key: string]: number } = {}
        topKeywords.forEach(keyword => {
          keywordTotals[keyword] = keywordTrendData30.reduce((sum, item) => sum + (item.keywords[keyword] || 0), 0)
        })
        
        console.log('关键词趋势数据已生成:', {
          dateRange: dateRange30.length,
          topKeywords: topKeywords.length,
          keywordTrendDataLength: keywordTrendData30.length,
          hasActualData,
          keywordTotals,
          sampleData: keywordTrendData30[0],
          trendKeywordStatsCount: trendKeywordStats.length,
          globalKeywordStatsCount: keywordStats.length
        })
        
        if (!hasActualData) {
          console.warn('⚠️ 警告：过去30天内没有关键词出现，图表将显示为空')
        }
      }

      // 趋势统计
      const trendMap = new Map<string, Map<string, number>>()
      const thirtyDaysAgoTimestamp = Math.floor(keywordTrendThirtyDaysAgo.getTime() / 1000)
      const trendDateRange: string[] = []
      for (let i = 29; i >= 0; i--) {
        const d = new Date(now.getTime() - i * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
        trendDateRange.push(d)
        trendMap.set(d, new Map())
      }
      
      const allMpNames = new Set<string>()
      articles.forEach((article: any) => {
        const publishTime = article.publish_time
        if (publishTime && typeof publishTime === 'number' && publishTime >= thirtyDaysAgoTimestamp) {
          const timestamp = publishTime.toString().length <= 10 ? publishTime * 1000 : publishTime
          const publishDate = new Date(timestamp)
          if (!isNaN(publishDate.getTime())) {
            const dateKey = publishDate.toISOString().split('T')[0]
            const mpName = article.mp_name || t('common.unknownError')
            allMpNames.add(mpName)
            const dayMap = trendMap.get(dateKey) || new Map()
            dayMap.set(mpName, (dayMap.get(mpName) || 0) + 1)
            trendMap.set(dateKey, dayMap)
          }
        }
      })

      const trendData: TrendData[] = trendDateRange.map(date => {
        const dayMap = trendMap.get(date) || new Map()
        const sources: { [mp_name: string]: number } = {}
        allMpNames.forEach(mpName => {
          sources[mpName] = dayMap.get(mpName) || 0
        })
        return { date, sources }
      })

      setDashboardData({
        stats: { totalArticles, totalSources, todayArticles, weekArticles },
        sourceStats,
        keywordStats,
        trendData,
        keywordTrendData: keywordTrendData30, // 存储完整的30天数据
        // 保存额外信息用于渲染判断
        _meta: {
          topKeywords,
          usingFallback
        }
      } as any)
    } catch (err) {
      console.error('计算统计数据失败:', err)
      throw err
    }
  }

  // --- 图表配置生成函数 ---

  const getColorPalette = (count: number): string[] => {
    const dark = isDarkMode()
    const colors = dark ? [
      'hsl(262.1, 83.3%, 70%)', 'hsl(221.2, 83.2%, 68%)', 'hsl(199.1, 89.1%, 65%)',
      'hsl(142.1, 76.2%, 55%)', 'hsl(38.7, 92%, 65%)', 'hsl(0, 84.2%, 70%)',
      'hsl(280, 70%, 65%)', 'hsl(240, 70%, 65%)', 'hsl(200, 80%, 65%)',
      'hsl(160, 60%, 60%)', 'hsl(330, 70%, 70%)', 'hsl(15, 90%, 70%)'
    ] : [
      'hsl(262.1, 83.3%, 57.8%)', 'hsl(221.2, 83.2%, 53.3%)', 'hsl(199.1, 89.1%, 48.2%)',
      'hsl(142.1, 76.2%, 36.3%)', 'hsl(38.7, 92%, 50%)', 'hsl(0, 84.2%, 60.2%)',
      'hsl(280, 70%, 50%)', 'hsl(240, 70%, 50%)', 'hsl(200, 80%, 50%)',
      'hsl(160, 60%, 45%)', 'hsl(330, 70%, 55%)', 'hsl(15, 90%, 55%)'
    ]
    const result: string[] = []
    for (let i = 0; i < count; i++) {
      result.push(colors[i % colors.length])
    }
    return result
  }

  const getSourceChartSpec = (sourceStats: SourceStats[]) => {
    const dark = isDarkMode()
    return {
      type: 'pie',
      background: 'transparent',
      data: {
        values: sourceStats.map(item => ({
          name: item.mp_name || item.mp_id,
          value: item.article_count
        }))
      },
      categoryField: 'name',
      valueField: 'value',
      outerRadius: 0.8,
      label: { visible: true, style: { fontSize: 12, fill: dark ? '#E5E7EB' : '#374151' } },
      tooltip: { mark: { content: [{ key: (d: any) => d.name, value: (d: any) => `${d.value} ${t('dashboard.tooltips.articles')}` }] } },
      color: getColorPalette(sourceStats.length)
    }
  }

  const getTrendChartSpec = (trendData: TrendData[]): any => {
    const dark = isDarkMode()
    const textColor = dark ? '#E5E7EB' : '#374151'
    const gridColor = dark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
    
    const allMpNames = new Set<string>()
    trendData.forEach(item => Object.keys(item.sources).forEach(n => { if (item.sources[n] > 0) allMpNames.add(n) }))
    const mpNamesArray = Array.from(allMpNames)
    
    const chartData: any[] = []
    trendData.forEach(item => {
      mpNamesArray.forEach(mpName => {
        const count = item.sources[mpName] || 0
        if (count > 0) chartData.push({ date: item.date, mp_name: mpName, count })
      })
    })
    
    const maxCount = Math.max(...chartData.map(item => item.count), 1)

    return {
      type: 'scatter',
      background: 'transparent',
      data: { values: chartData },
      xField: 'date',
      yField: 'count',
      seriesField: 'mp_name',
      sizeField: 'count',
      size: { type: 'linear', range: [10, 40], domain: [0, maxCount] },
      point: { visible: true, style: { fillOpacity: 0.7, strokeWidth: 1.5 } },
      color: getColorPalette(mpNamesArray.length),
      axes: [
        {
          orient: 'bottom' as const, type: 'band' as const,
          domainLine: { visible: true, style: { stroke: gridColor } },
          grid: { visible: true, style: { stroke: gridColor } },
          tick: { visible: true, style: { stroke: gridColor } },
          label: { visible: true, style: { fill: textColor, fontSize: 11 }, formatMethod: (v: string, i: number) => i % 5 === 0 ? v : '' }
        },
        {
          orient: 'left' as const, type: 'linear' as const, zero: true,
          domainLine: { visible: true, style: { stroke: gridColor } },
          grid: { visible: true, style: { stroke: gridColor } },
          tick: { visible: true, style: { stroke: gridColor } },
          label: { visible: true, style: { fill: textColor, fontSize: 12 } }
        }
      ],
      legends: { visible: true, orient: 'top' as const, position: 'start' as const, item: { label: { style: { fill: textColor, fontSize: 11 } } } },
      tooltip: {
        mark: {
          content: [
            { key: () => t('dashboard.tooltips.date'), value: (d: any) => d.date },
            { key: () => t('dashboard.tooltips.source'), value: (d: any) => d.mp_name },
            { key: () => t('dashboard.tooltips.articleCount'), value: (d: any) => `${d.count} ${t('dashboard.tooltips.articles')}` }
          ]
        }
      }
    }
  }

  const getKeywordStackChartSpec = (keywordTrendData: KeywordTrendData[], topKeywords: string[]) => {
    const dark = isDarkMode()
    const textColor = dark ? '#E5E7EB' : '#374151'
    const gridColor = dark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
    
    const chartData = keywordTrendData.flatMap(item => topKeywords.map(keyword => ({
      date: item.date, keyword, count: item.keywords[keyword] || 0
    })))

    // 检查是否有实际数据（至少有一个 count > 0）
    const hasData = chartData.some(item => item.count > 0)
    if (!hasData) {
      console.warn('关键词图表数据为空或全为0:', {
        chartDataLength: chartData.length,
        topKeywords,
        sampleData: chartData.slice(0, 5)
      })
      return null
    }
    
    console.log('关键词堆叠图配置:', {
      dataPoints: chartData.length,
      dates: keywordTrendData.length,
      keywords: topKeywords.length,
      hasData
    })

    const spec = {
      type: 'bar',
      background: 'transparent',
      data: { values: chartData },
      xField: 'date', 
      yField: 'count', 
      seriesField: 'keyword', 
      stack: true,
      bar: { style: { cornerRadius: 4 } },
      color: getColorPalette(topKeywords.length),
      tooltip: {
        mark: {
          content: [
            { key: () => t('dashboard.tooltips.date'), value: (d: any) => d.date },
            { key: () => t('dashboard.tooltips.keyword'), value: (d: any) => d.keyword },
            { key: () => t('dashboard.tooltips.occurrenceCount'), value: (d: any) => `${d.count} ${t('dashboard.tooltips.times')}` }
          ]
        }
      },
      axes: [
        {
          orient: 'bottom' as const, 
          type: 'band' as const,
          domainLine: { visible: true, style: { stroke: gridColor } },
          grid: { visible: true, style: { stroke: gridColor } },
          tick: { visible: false },
          label: { 
            visible: true, 
            style: { fontSize: 9, angle: -45, fill: textColor },
            formatMethod: (v: string, i: number) => {
              // 根据数据点数量动态调整显示策略
              const total = keywordTrendData.length
              if (total <= 7) {
                // 7天或更少：显示所有日期
                return v
              } else if (total <= 14) {
                // 14天或更少：每2个显示一个
                return i % 2 === 0 ? v : ''
              } else if (total <= 30) {
                // 30天：显示所有日期标签（每天都有）
                return v
              } else {
                // 超过30天：每5个显示一个
                return i % 5 === 0 ? v : ''
              }
            }
          }
        },
        {
          orient: 'left' as const, 
          type: 'linear' as const,
          domainLine: { visible: true, style: { stroke: gridColor } },
          grid: { visible: true, style: { stroke: gridColor } },
          tick: { visible: true, style: { stroke: gridColor } },
          label: { visible: true, style: { fill: textColor, fontSize: 12 } }
        }
      ],
      legends: { 
        visible: true, 
        orient: 'top' as const, 
        position: 'start' as const, 
        item: { label: { style: { fill: textColor, fontSize: 12 } } } 
      }
    }
    return spec
  }

  const getKeywordLineChartSpec = (keywordTrendData: KeywordTrendData[], topKeywords: string[]) => {
    const dark = isDarkMode()
    const textColor = dark ? '#E5E7EB' : '#374151'
    const gridColor = dark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
    
    const chartData = keywordTrendData.flatMap(item => topKeywords.map(keyword => ({
      date: item.date, keyword, count: item.keywords[keyword] || 0
    })))

    // 检查是否有实际数据（至少有一个 count > 0）
    const hasData = chartData.some(item => item.count > 0)
    if (!hasData) {
      console.warn('关键词折线图数据为空或全为0:', {
        chartDataLength: chartData.length,
        topKeywords,
        sampleData: chartData.slice(0, 5)
      })
      return null
    }
    
    console.log('关键词折线图配置:', {
      dataPoints: chartData.length,
      dates: keywordTrendData.length,
      keywords: topKeywords.length,
      hasData
    })

    return {
      type: 'line',
      background: 'transparent',
      data: { values: chartData },
      xField: 'date', 
      yField: 'count', 
      seriesField: 'keyword',
      point: { visible: true, style: { size: 3 } },
      line: { style: { lineWidth: 2 } },
      color: getColorPalette(topKeywords.length),
      tooltip: {
        mark: {
          content: [
            { key: () => t('dashboard.tooltips.date'), value: (d: any) => d.date },
            { key: () => t('dashboard.tooltips.keyword'), value: (d: any) => d.keyword },
            { key: () => t('dashboard.tooltips.occurrenceCount'), value: (d: any) => `${d.count} ${t('dashboard.tooltips.times')}` }
          ]
        }
      },
      axes: [
        {
          orient: 'bottom' as const, 
          type: 'band' as const,
          domainLine: { visible: true, style: { stroke: gridColor } },
          grid: { visible: true, style: { stroke: gridColor } },
          tick: { visible: false },
          label: { 
            visible: true, 
            style: { fontSize: 9, angle: -45, fill: textColor },
            formatMethod: (v: string, i: number) => {
              // 根据数据点数量动态调整显示策略
              const total = keywordTrendData.length
              if (total <= 7) {
                // 7天或更少：显示所有日期
                return v
              } else if (total <= 14) {
                // 14天或更少：每2个显示一个
                return i % 2 === 0 ? v : ''
              } else if (total <= 30) {
                // 30天：显示所有日期标签（每天都有）
                return v
              } else {
                // 超过30天：每5个显示一个
                return i % 5 === 0 ? v : ''
              }
            }
          }
        },
        {
          orient: 'left' as const, 
          type: 'linear' as const,
          domainLine: { visible: true, style: { stroke: gridColor } },
          grid: { visible: true, style: { stroke: gridColor } },
          tick: { visible: true, style: { stroke: gridColor } },
          label: { visible: true, style: { fill: textColor, fontSize: 12 } }
        }
      ],
      legends: { 
        visible: true, 
        orient: 'top' as const, 
        position: 'start' as const, 
        item: { label: { style: { fill: textColor, fontSize: 12 } } } 
      }
    }
  }

  // --- 渲染层 ---

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive" className="m-5">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  const { stats, sourceStats, keywordStats, trendData, keywordTrendData: keywordTrendData30 = [] } = dashboardData || {
    stats: { totalArticles: 0, totalSources: 0, todayArticles: 0, weekArticles: 0 },
    sourceStats: [], keywordStats: [], trendData: [], keywordTrendData: []
  }

  // 从元数据中获取 topKeywords，如果没有则使用全局统计的前10个作为备选
  const meta = (dashboardData as any)?._meta
  const topKeywords = meta?.topKeywords || keywordStats.slice(0, 10).map(k => k.keyword)

  // 根据选择的时间范围过滤趋势数据
  const keywordTrendData = keywordTrendData30.slice(-keywordDateRange)

  // 调试：检查趋势数据是否有实际值
  if (keywordStats.length > 0 && keywordTrendData.length > 0) {
    const totalTrendCount = keywordTrendData.reduce((sum, item) => {
      return sum + Object.values(item.keywords).reduce((s, v) => s + v, 0)
    }, 0)
    if (totalTrendCount === 0) {
      console.warn('热门关键词趋势数据全为0:', {
        topKeywords,
        trendDataLength: keywordTrendData.length,
        sampleData: keywordTrendData[0],
        metaProvided: !!meta
      })
    }
  }
  

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 text-foreground">{t('dashboard.title')}</h1>
        <p className="text-muted-foreground text-sm">{t('dashboard.subtitle')}</p>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-6">
            <Statistic title={t('dashboard.stats.totalArticles')} value={stats.totalArticles} prefix={<FileText className="h-5 w-5 text-primary" />} />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Statistic title={t('dashboard.stats.totalSources')} value={stats.totalSources} prefix={<User className="h-5 w-5 text-primary" />} />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Statistic title={t('dashboard.stats.todayArticles')} value={stats.todayArticles} prefix={<Calendar className="h-5 w-5 text-primary" />} />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Statistic title={t('dashboard.stats.weekArticles')} value={stats.weekArticles} prefix={<Flame className="h-5 w-5 text-primary" />} />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <Card className="h-[400px]">
          <CardHeader>
            <CardTitle className="text-base font-semibold">{t('dashboard.charts.sourceDistribution')}</CardTitle>
          </CardHeader>
          <CardContent>
            {sourceStats.length > 0 ? (
              <Suspense fallback={<div className="flex justify-center items-center h-[320px]"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>}>
                <VChart spec={getSourceChartSpec(sourceStats)} style={{ height: '320px' }} />
              </Suspense>
            ) : (
              <div className="flex justify-center items-center h-[320px] text-muted-foreground">{t('dashboard.charts.noData')}</div>
            )}
          </CardContent>
        </Card>

        <Card className="h-[400px]">
          <CardHeader>
            <CardTitle className="text-base font-semibold">{t('dashboard.charts.fetchTrend')}</CardTitle>
          </CardHeader>
          <CardContent>
            {trendData.length > 0 && trendData.some(item => Object.values(item.sources).some(c => c > 0)) ? (
              <Suspense fallback={<div className="flex justify-center items-center h-[320px]"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>}>
                <VChart spec={getTrendChartSpec(trendData)} style={{ height: '320px' }} />
              </Suspense>
            ) : (
              <div className="flex justify-center items-center h-[320px] text-muted-foreground">{t('dashboard.charts.noData')}</div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="mb-6">
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center w-full">
              <CardTitle className="text-base font-semibold">{t('dashboard.charts.hotKeywords')}</CardTitle>
              <div className="flex gap-3 items-center">
                <ButtonGroup
                  value={keywordDateRange.toString()}
                  onValueChange={(v: string) => {
                    const newRange = parseInt(v) as 7 | 30;
                    setKeywordDateRange(newRange);
                  }}
                  options={[
                    { value: "7", label: t('dashboard.controls.dateRange.7days') },
                    { value: "30", label: t('dashboard.controls.dateRange.30days') }
                  ]}
                  size="sm"
                />
                {keywordTrendData.length > 0 && (
                  <ButtonGroup
                    value={keywordChartType}
                    onValueChange={(v: string) => setKeywordChartType(v as any)}
                    options={[
                      { value: "stack", label: t('dashboard.controls.chartType.stack') },
                      { value: "line", label: t('dashboard.controls.chartType.line') }
                    ]}
                    size="sm"
                  />
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {keywordStats.length > 0 ? (
              <>
                {/* 标签云 - 始终显示 */}
                <div className="mb-5 flex flex-wrap gap-3 animate-in fade-in zoom-in duration-300">
                  {keywordStats.slice(0, 20).map((item, index) => (
                    <Badge key={index} variant={index < 3 ? "default" : "secondary"} className="text-sm px-4 py-2 font-normal">
                      {item.keyword} ({item.count})
                    </Badge>
                  ))}
                </div>

                {/* 趋势图 - 始终显示 */}
                {(
                  <>
                    {keywordTrendData && keywordTrendData.length > 0 && topKeywords && topKeywords.length > 0 ? (() => {
                      // 检查是否有实际数据
                      const hasActualData = keywordTrendData.some(item => 
                        topKeywords.some((keyword: string) => (item.keywords[keyword] || 0) > 0)
                      )
                      
                      // 获取元数据（如果存在）
                      const meta = (dashboardData as any)?._meta
                      const usingFallback = meta?.usingFallback || false
                      
                      // 如果使用了备选关键词且没有实际数据，仍然显示图表（即使数据为0）
                      // 这样用户至少能看到图表结构，知道系统在工作
                      if (!hasActualData && !usingFallback) {
                        return (
                          <div className="text-center text-muted-foreground py-10">
                            <div>{t('dashboard.charts.noTrendData')}</div>
                            <div className="text-sm mt-2">{t('dashboard.charts.waitForData')}</div>
                          </div>
                        )
                      }
                      
                      const chartSpec = keywordChartType === 'stack' 
                        ? getKeywordStackChartSpec(keywordTrendData, topKeywords) 
                        : getKeywordLineChartSpec(keywordTrendData, topKeywords)
                      
                      if (!chartSpec) {
                        return (
                          <div className="text-center text-muted-foreground py-10">
                            <div>{t('dashboard.charts.chartConfigFailed')}</div>
                            <div className="text-sm mt-2">数据: {keywordTrendData.length} 天, {topKeywords.length} 个关键词</div>
                          </div>
                        )
                      }
                      
                      return (
                        <div className="mt-6 h-[400px] animate-in fade-in slide-in-from-bottom-2 duration-300">
                          <ChartErrorBoundary>
                            <Suspense fallback={<div className="flex justify-center items-center h-[400px]"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>}>
                              <VChart 
                                spec={chartSpec} 
                                style={{ height: '400px', width: '100%' }} 
                                onError={(error: any) => {
                                  console.error('VChart 渲染错误:', error)
                                }}
                              />
                            </Suspense>
                          </ChartErrorBoundary>
                        </div>
                      )
                    })() : (() => {
                      return (
                        <div className="text-center text-muted-foreground py-10">
                          {!topKeywords || topKeywords.length === 0 ? (
                            <div>{t('dashboard.charts.noKeywordData')}</div>
                          ) : !keywordTrendData || keywordTrendData.length === 0 ? (
                            <div>{t('dashboard.charts.waitForData')}</div>
                          ) : (
                            <div>{t('dashboard.charts.dataLoading')}</div>
                          )}
                        </div>
                      );
                    })()}
                  </>
                )}
              </>
            ) : (
              <div className="text-center text-muted-foreground py-10">{t('dashboard.charts.noData')}</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default Dashboard