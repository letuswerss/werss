import http from './http'
import type { MessageTask, MessageTaskUpdate } from '@/types/messageTask'

export const listMessageTasks = (params?: { offset?: number; limit?: number }) => {
  console.log(params)
  const apiParams = {
    offset: (params?.offset || 0) ,
    limit: params?.limit || 10
  }
  return http.get<MessageTask>('/wx/message_tasks', { params: apiParams })
}
export const getMessageTask = (id: string) => {
  return http.get<MessageTask>(`/wx/message_tasks/${id}`)
}
export const RunMessageTask = (id: string,isTest:boolean=false) => {
  return http.get<MessageTask>(`/wx/message_tasks/${id}/run?isTest=${isTest}`)
}

export const createMessageTask = (data: MessageTaskUpdate) => {
  return http.post('/wx/message_tasks', data)
}

export const updateMessageTask = (id: string, data: MessageTaskUpdate) => {
  return http.put(`/wx/message_tasks/${id}`, data)
}
export const FreshJobApi = () => {
  return http.put(`/wx/message_tasks/job/fresh`)
}
export const FreshJobByIdApi = (id: string, data: MessageTaskUpdate) => {
  return http.put(`/wx/message_tasks/job/fresh/${id}`, data)
}

export const deleteMessageTask = (id: string) => {
  return http.delete(`/wx/message_tasks/${id}`)
}