import http from './http'
import type { Tag, TagCreate } from '@/types/tagManagement'

export const listTags = (params?: { offset?: number; limit?: number }) => {
  return http.get<Tag[]>('/wx/tags', { 
    params: {
      offset: params?.offset || 0,
      limit: params?.limit || 100
    }
  })
}

export const getTag = (id: string) => {
  return http.get<Tag>(`/wx/tags/${id}`)
}

export const createTag = (data: TagCreate) => {
  return http.post('/wx/tags', data)
}

export const updateTag = (id: string, data: TagCreate) => {
  return http.put(`/wx/tags/${id}`, data)
}

export const updateTagStatus = (tag: Tag, status: number) => {
  return updateTag(tag.id, {
    name: tag.name,
    cover: tag.cover || '',
    intro: tag.intro || '',
    mps_id: tag.mps_id || '[]',
    is_custom: tag.is_custom || false,
    status
  })
}

export const deleteTag = (id: string) => {
  return http.delete(`/wx/tags/${id}`)
}

export const batchDeleteTags = (tagIds: string[]) => {
  // 使用 DELETE 方法和查询参数，批量删除在外侧路由
  const params = tagIds.map(id => `tag_ids=${encodeURIComponent(id)}`).join('&')
  return http.delete(`/wx/tags?${params}`)
}
