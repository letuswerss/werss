import http from './http'
import { Message } from '@/utils/message'
export interface LoginParams {
  username: string
  password: string
}

export interface LoginResult {
  access_token: string
  token_type: string
}

export const login = (data: LoginParams) => {
  const formData = new URLSearchParams()
  formData.append('username', data.username)
  formData.append('password', data.password)
  return http.post<LoginResult>('/wx/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  })
}

export interface VerifyResult {
  is_valid: boolean
  username: string
  expires_at?: number
}

export const verifyToken = () => {
  return http.get<VerifyResult>('/wx/auth/verify')
}
/**
 * 将后端返回的二维码地址转为浏览器可加载的绝对 URL。
 * 开发环境页面在 Vite（如 5174），后端返回的 `/static/wx_qrcode.png` 会错误地请求到前端端口；
 * 若配置了 `VITE_API_BASE_URL=http://localhost:8001/`，则拼成后端上的静态资源地址。
 */
export function resolveQrCodeImageUrl(code: string | null | undefined): string {
  if (code == null || typeof code !== 'string') return ''
  const trimmed = code.trim()
  if (!trimmed) return ''
  if (/^https?:\/\//i.test(trimmed)) return trimmed
  const base = import.meta.env.VITE_API_BASE_URL || ''
  if (trimmed.startsWith('/') && (base.startsWith('http://') || base.startsWith('https://'))) {
    try {
      return new URL(trimmed, base.endsWith('/') ? base : `${base}/`).href
    } catch {
      return trimmed
    }
  }
  return trimmed
}

export const QRCode = () => {
  return http.get('/wx/auth/qr/code').then((res: { code?: string; msg?: string; is_exists?: boolean }) => {
    const url = resolveQrCodeImageUrl(res?.code)
    if (!url) {
      return Promise.reject(new Error((res as { msg?: string })?.msg || '获取二维码失败'))
    }
    return { ...res, code: url }
  })
}
let interval_status_Id:number=0
export const checkQRCodeStatus = () => {
  return new Promise((resolve, reject) => {
     if (interval_status_Id) {
      clearInterval(interval_status_Id);
      interval_status_Id = 0;
    }
      interval_status_Id = setInterval(() => {
        http.get('/wx/auth/qr/status').then(response => {
          if(response?.login_status){
            Message.success("授权成功")
            clearInterval(interval_status_Id)
            resolve(response)
          }
        }).catch(err => {
          // clearInterval(intervalId)
          // reject(err)
        })
      }, 3000)
  })
}
export const refreshToken = () => {
  return http.post<LoginResult>('/wx/auth/refresh')
}

export const logout = () => {
  return http.post('/wx/auth/logout')
}

export const getCurrentUser = () => {
  return http.get('/wx/user')
}