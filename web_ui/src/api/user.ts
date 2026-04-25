import http from './http'

export interface UserInfo {
  username: string
  nickname: string
  email: string
  avatar: string
  role: string
  is_active: boolean
  created_at: string
}

export interface UpdateUserParams {
  nickname?: string
  email?: string
  avatar?: string
  password?: string
  is_active?: boolean
}

export const getUserInfo = () => {
  return http.get<{code: number, data: UserInfo}>('/wx/user')
}

export const updateUserInfo = (data: UpdateUserParams) => {
  return http.put<{code: number, message: string}>('/wx/user', data)
}

export interface ChangePasswordParams {
  old_password: string
  new_password: string
}

export const changePassword = (data: ChangePasswordParams) => {
  return http.put<{code: number, message: string}>('/wx/user/password', data, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  })
}

// 保持旧方法向后兼容
export const changePasswordLegacy = (newPassword: string) => {
  return updateUserInfo({ password: newPassword })
}

export const toggleUserStatus = (active: boolean) => {
  return updateUserInfo({ is_active: active })
}

export const uploadAvatar = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<{code: number, url: string}>('/wx/user/avatar', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
