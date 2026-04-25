import http from './http'
import type {
  ApiKey,
  CreateApiKeyParams,
  UpdateApiKeyParams,
  ApiKeyListResponse,
  ApiKeyLogListResponse
} from '@/types/apiKey'

/**
 * 创建 API Key
 */
export const createApiKey = (data: CreateApiKeyParams) => {
  return http.post<{ code: number; data: ApiKey; message: string }>('/wx/api-keys', data)
}

/**
 * 获取 API Key 列表
 */
export const getApiKeys = (params?: { page?: number; pageSize?: number }) => {
  const page = params?.page ?? 1
  const pageSize = params?.pageSize ?? 10
  return http.get<{ code: number; data: ApiKeyListResponse }>('/wx/api-keys', {
    params: {
      page,
      page_size: pageSize
    }
  })
}

/**
 * 获取 API Key 详情
 */
export const getApiKey = (apiKeyId: string) => {
  return http.get<{ code: number; data: ApiKey }>(`/wx/api-keys/${apiKeyId}`)
}

/**
 * 更新 API Key
 */
export const updateApiKey = (apiKeyId: string, data: UpdateApiKeyParams) => {
  return http.put<{ code: number; data: ApiKey; message: string }>(`/wx/api-keys/${apiKeyId}`, data)
}

/**
 * 删除 API Key
 */
export const deleteApiKey = (apiKeyId: string) => {
  return http.delete<{ code: number; message: string }>(`/wx/api-keys/${apiKeyId}`)
}

/**
 * 获取 API Key 使用日志
 */
export const getApiKeyLogs = (apiKeyId: string, params?: { page?: number; pageSize?: number }) => {
  const page = params?.page ?? 1
  const pageSize = params?.pageSize ?? 10
  return http.get<{ code: number; data: ApiKeyLogListResponse }>(`/wx/api-keys/${apiKeyId}/logs`, {
    params: {
      page,
      page_size: pageSize
    }
  })
}

/**
 * 重新生成 API Key
 */
export const regenerateApiKey = (apiKeyId: string) => {
  return http.post<{ code: number; data: ApiKey; message: string }>(`/wx/api-keys/${apiKeyId}/regenerate`)
}
