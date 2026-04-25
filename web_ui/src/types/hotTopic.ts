export interface HotTopic {
  id: string
  topic_name: string
  summary: string
  signals: string[]
  article_count: number
  article_ids: string[]
  representative_titles?: string[]
}

export interface HotTopicsResponse {
  run_id: string | null
  window_days: number
  model_name?: string
  created_at?: string
  topics: HotTopic[]
}

export interface HotTopicRunDetail {
  id: string
  window_days: number
  article_count: number
  status: string
  model_name?: string
  prompt_version?: string
  created_at?: string
  error_message?: string
  topics: HotTopic[]
}

export interface RebuildHotTopicsParams {
  window_days?: number
  max_topics?: number
}

export interface RebuildHotTopicsResponse {
  run_id: string
  topic_count: number
  message: string
}
