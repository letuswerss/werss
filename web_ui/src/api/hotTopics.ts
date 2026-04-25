import http from './http'
import type {
  HotTopicsResponse,
  HotTopicRunDetail,
  RebuildHotTopicsParams,
  RebuildHotTopicsResponse,
} from '@/types/hotTopic'

export const getRecentHotTopics = () => {
  return http.get<HotTopicsResponse>('/wx/hot-topics/recent')
}

export const rebuildHotTopics = (params: RebuildHotTopicsParams) => {
  return http.post<RebuildHotTopicsResponse>('/wx/hot-topics/rebuild', undefined, {
    params,
    timeout: 15 * 60 * 1000, // 15 分钟超时
  })
}

export const getHotTopicRun = (runId: string) => {
  return http.get<HotTopicRunDetail>(`/wx/hot-topics/runs/${runId}`)
}
