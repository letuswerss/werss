import http from './http'
import type { ConfigManagement, ConfigManagementCreate, ConfigManagementUpdate } from '@/types/configManagement'

export const listConfigs = (params?: { page?: number; pageSize?: number }) => {
  const apiParams = {
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<ConfigManagement>('/wx/configs', { params: apiParams })
}
export const getConfig = (key: string) => {
  return http.get<ConfigManagement>(`/wx/configs/${key}`)
}



export const createConfig = (data: ConfigManagementCreate) => {
  return http.post('/wx/configs', data)
}

export const updateConfig = (key: string, data: ConfigManagementUpdate) => {
  return http.put(`/wx/configs/${key}`, data)
}

export const deleteConfig = (key: string) => {
  return http.delete(`/wx/configs/${key}`)
}