import http from './http'
import type { NotifyTask, NotifyTaskCreate } from '@/types/notifyTask'

export const listNotifyTasks = (params?: { offset?: number; limit?: number }) => {
  const apiParams = {
    offset: params?.offset || 0,
    limit: params?.limit || 10,
  }
  return http.get<NotifyTask>('/wx/notify_tasks', { params: apiParams })
}

export const getNotifyTask = (id: string) => {
  return http.get<NotifyTask>(`/wx/notify_tasks/${id}`)
}

export const createNotifyTask = (data: NotifyTaskCreate) => {
  return http.post('/wx/notify_tasks', data)
}

export const updateNotifyTask = (id: string, data: NotifyTaskCreate) => {
  return http.put(`/wx/notify_tasks/${id}`, data)
}

export const deleteNotifyTask = (id: string) => {
  return http.delete(`/wx/notify_tasks/${id}`)
}

export const runNotifyTask = (id: string) => {
  return http.get(`/wx/notify_tasks/${id}/run`)
}

export const reloadNotifyJobs = () => {
  return http.put(`/wx/notify_tasks/job/fresh`)
}
