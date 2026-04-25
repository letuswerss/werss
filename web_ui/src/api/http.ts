import axios from 'axios'
import { getToken } from '@/utils/auth'
import { Message } from '@/utils/message'
// 创建axios实例
const http = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || '') + 'api/v1/',
  timeout: 100000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// 请求拦截器
http.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
http.interceptors.response.use(
  response => {
    // 处理标准响应格式
    if (response.data?.code === 0) {
      return response.data?.data||response.data?.detail||response.data||response
    }
    if(response.data?.code==401){
      window.location.href = "/login"
      return Promise.reject("未登录或登录已过期，请重新登录。")
    }
    const data=response.data?.detail||response.data
    const errorMsg = data?.message || '请求失败'
    // 对于 40402（刷新限制），不显示错误消息，让调用方自己处理
    if(response.headers['content-type']==='application/json' && data?.code !== 40402) {
      Message.error(errorMsg)
    }else{
      return response.data
    }
    return Promise.reject(response.data)
  },
  error => {
     if(error.status==401 || error?.response?.status === 401){
      window.location.href = "/login"
    } 
    // console.log(error)
    // 统一错误处理
    // 对于 404 错误，返回原始 error 对象，让调用方可以检查 status
    if (error?.response?.status === 404) {
      return Promise.reject(error)
    }
    // Message.error(errorMsg)
    return Promise.reject(error)
  }
)

export default http