// 设置管理工具函数

import { applyTheme, readPersistedTheme } from '@/store'

export interface AppSettings {
  watermarkEnabled: boolean
  darkMode: boolean
}

const SETTINGS_KEY = 'app_settings'

// 默认设置
const defaultSettings: AppSettings = {
  watermarkEnabled: true,
  darkMode: false
}

// 获取设置
export const getSettings = (): AppSettings => {
  try {
    const stored = localStorage.getItem(SETTINGS_KEY)
    if (stored) {
      return { ...defaultSettings, ...JSON.parse(stored) }
    }
  } catch (error) {
    console.error('读取设置失败:', error)
  }
  return defaultSettings
}

// 保存设置
export const saveSettings = (settings: Partial<AppSettings>): void => {
  try {
    const current = getSettings()
    const newSettings = { ...current, ...settings }
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(newSettings))

    // 触发设置变更事件，通知其他组件
    window.dispatchEvent(new CustomEvent('settingsChanged', { detail: newSettings }))
  } catch (error) {
    console.error('保存设置失败:', error)
  }
}

// 更新单个设置项
export const updateSetting = <K extends keyof AppSettings>(
  key: K,
  value: AppSettings[K]
): void => {
  saveSettings({ [key]: value })
}

// 初始化设置（在应用启动时调用）
export const initSettings = (): void => {
  const theme = readPersistedTheme()
  applyTheme(theme)
  try {
    localStorage.setItem('vite-ui-theme', theme)
  } catch {
    /* ignore */
  }
}

