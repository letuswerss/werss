import i18n from '@/i18n/config'

/**
 * 翻译页面（已废弃，现在使用 react-i18next 自动处理）
 * 保留此函数以保持向后兼容
 */
export const translatePage = () => {
  i18n.changeLanguage('zh-CN')
}

/**
 * 设置当前语言
 */
export const setCurrentLanguage = () => {
  i18n.changeLanguage('zh-CN')
}

/**
 * 获取当前语言
 */
export const getCurrentLanguage = (): string => {
  return 'zh-CN'
}
