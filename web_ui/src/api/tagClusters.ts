import http from './http'
import type {
  TagClusterDetail,
  TagClusterListResponse,
  SimilarTagItem,
} from '@/types/tagCluster'

export const listTagClusters = (params?: { offset?: number; limit?: number }) => {
  return http.get<TagClusterListResponse>('/wx/tag-clusters', {
    params: {
      offset: params?.offset || 0,
      limit: params?.limit || 50,
    },
  })
}

export const getTagCluster = (id: string) => {
  return http.get<TagClusterDetail>(`/wx/tag-clusters/${id}`)
}

export const exportTagCluster = (id: string) => {
  return http.get(`/wx/tag-clusters/${id}/export`, {
    responseType: 'blob',
  })
}

export const getSimilarTags = (tagId: string, limit = 10) => {
  return http.get<SimilarTagItem[]>(`/wx/tag-clusters/similar/${tagId}`, {
    params: { limit },
  })
}

export const rebuildTagClusters = () => {
  return http.post('/wx/tag-clusters/rebuild', undefined, {
    timeout: 15 * 60 * 1000,
  })
}
