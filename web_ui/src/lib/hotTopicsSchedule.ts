/**
 * 五段 cron：分 时 日 月 周（与后端 TaskScheduler 一致）
 */
export type CronPresetId =
  | 'every_1h'
  | 'every_2h'
  | 'every_3h'
  | 'every_6h'
  | 'every_12h'
  | 'daily'
  | 'custom'

export function cronFromPreset(preset: CronPresetId, dailyHour: number): string {
  switch (preset) {
    case 'every_1h':
      return '0 * * * *'
    case 'every_2h':
      return '0 */2 * * *'
    case 'every_3h':
      return '0 */3 * * *'
    case 'every_6h':
      return '0 */6 * * *'
    case 'every_12h':
      return '0 */12 * * *'
    case 'daily': {
      const h = Math.max(0, Math.min(23, Math.floor(dailyHour)))
      return `0 ${h} * * *`
    }
    case 'custom':
    default:
      return '0 9 * * *'
  }
}

export function detectCronPreset(cron: string): { preset: CronPresetId; dailyHour: number } {
  const t = cron.trim().replace(/\s+/g, ' ')
  if (t === '0 * * * *') return { preset: 'every_1h', dailyHour: 9 }
  if (t === '0 */2 * * *') return { preset: 'every_2h', dailyHour: 9 }
  if (t === '0 */3 * * *') return { preset: 'every_3h', dailyHour: 9 }
  if (t === '0 */6 * * *') return { preset: 'every_6h', dailyHour: 9 }
  if (t === '0 */12 * * *') return { preset: 'every_12h', dailyHour: 9 }
  const m = t.match(/^0 (\d{1,2}) \* \* \*$/)
  if (m) return { preset: 'daily', dailyHour: Math.min(23, Math.max(0, parseInt(m[1], 10))) }
  return { preset: 'custom', dailyHour: 9 }
}
