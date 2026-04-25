export const RES_BASE_URL = "/static/res/logo/"

// 微信图片/头像 CDN 域名集合（与后端 apis/res.py 的白名单保持一致）
const WX_IMAGE_HOSTS = [
  'mmbiz.qpic.cn',
  'mmbiz.qlogo.cn',
  'mmecoa.qpic.cn',
  'wx.qlogo.cn',
  'thirdwx.qlogo.cn',
]

const WX_HOST_REGEX = new RegExp(
  `^https?://(?:${WX_IMAGE_HOSTS.map(h => h.replace(/\./g, '\\.')).join('|')})/`,
  'i',
)

/**
 * 头像 URL 适配：
 * - null / undefined / 非字符串：原样返回，调用方负责降级到 fallback。
 * - 已经带 `/static/res/logo/` 前缀：原样返回，避免双重前缀。
 * - 微信图片 CDN（http/https）：自动加上代理前缀，通过本服务统一加载。
 * - 其它 http/https URL（含已落到 MinIO 的自建对象）：原样返回，浏览器直连。
 * - 站内相对路径：原样返回。
 */
export const Avatar = (url: unknown): string => {
  if (typeof url !== 'string' || !url) return ''
  const trimmed = url.trim()
  if (!trimmed) return ''
  if (trimmed.startsWith(RES_BASE_URL) || trimmed.startsWith('/static/res/logo/')) return trimmed
  if (WX_HOST_REGEX.test(trimmed)) return `${RES_BASE_URL}${trimmed}`
  return trimmed
}