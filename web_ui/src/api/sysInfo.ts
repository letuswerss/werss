import http from './http'

export const getSysInfo = async (): Promise<any> => {
  const data = await http.get('/wx/sys/info')
  return data
}

export const getSysResources = async (): Promise<any> => {
  const data = await http.get('/wx/sys/resources')
  return data
}