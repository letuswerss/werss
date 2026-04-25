/**
 * API Key 相关类型定义
 */

/**
 * API Key 实体接口
 */
export interface ApiKey {
  id: string
  name: string
  user_id: string
  permissions: string | null
  is_active: boolean
  last_used_at: string | null
  created_at: string
  updated_at: string
  key?: string // 只在创建/重新生成时返回
}

/**
 * API Key 创建请求参数
 */
export interface CreateApiKeyParams {
  name: string
  permissions?: string | null
}

/**
 * API Key 更新请求参数
 */
export interface UpdateApiKeyParams {
  name?: string
  permissions?: string | null
  is_active?: boolean
}

/**
 * API Key 列表响应
 */
export interface ApiKeyListResponse {
  total: number
  page: number
  page_size: number
  list: ApiKey[]
}

/**
 * API Key 使用日志实体接口
 */
export interface ApiKeyLog {
  id: string
  api_key_id: string
  endpoint: string
  method: string
  ip_address: string | null
  user_agent: string | null
  status_code: number
  created_at: string
}

/**
 * API Key 使用日志列表响应
 */
export interface ApiKeyLogListResponse {
  total: number
  page: number
  page_size: number
  list: ApiKeyLog[]
}



