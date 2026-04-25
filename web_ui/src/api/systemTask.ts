import http from './http'

export interface SystemTaskItem {
  key: string
  name: string
  type: 'table' | 'config'
  enabled: boolean
  summary: string
  cron: string
  next_run?: string | null
  manage_path: string
}

export interface ArticleRetentionConfig {
  enabled: boolean
  cron: string
  days: number
  basis: 'created_at' | 'publish_time'
  next_run?: string | null
}

export interface HotTopicsScheduleConfig {
  enabled: boolean
  cron: string
  window_days: number
  max_topics: number
  next_run?: string | null
}

export interface SystemTaskOverview {
  tasks: SystemTaskItem[]
  hot_topics?: HotTopicsScheduleConfig
  article_retention: ArticleRetentionConfig
}

export interface ArticleRetentionUpdate {
  enabled?: boolean
  cron?: string
  days?: number
  basis?: 'created_at' | 'publish_time'
}

export interface HotTopicsScheduleUpdate {
  enabled?: boolean
  cron?: string
  window_days?: number
  max_topics?: number
}

export const getSystemTasks = () => {
  return http.get('/wx/system_tasks') as Promise<SystemTaskOverview>
}

export const updateArticleRetention = (data: ArticleRetentionUpdate) => {
  return http.put('/wx/system_tasks/article-retention', data) as Promise<SystemTaskOverview>
}

export const runArticleRetention = () => {
  return http.post('/wx/system_tasks/article-retention/run')
}

export const updateHotTopicsSchedule = (data: HotTopicsScheduleUpdate) => {
  return http.put('/wx/system_tasks/hot-topics', data) as Promise<SystemTaskOverview>
}

export const deleteHotTopicsSchedule = () => {
  return http.delete('/wx/system_tasks/hot-topics') as Promise<SystemTaskOverview>
}

export const runHotTopicsNow = () => {
  return http.post('/wx/system_tasks/hot-topics/run') as Promise<{
    run_id: string
    topic_count: number
  }>
}

export const reloadSystemTasks = () => {
  return http.put('/wx/system_tasks/reload') as Promise<SystemTaskOverview>
}
