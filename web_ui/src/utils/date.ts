import dayjs from 'dayjs'

export const formatDateTime = (date: string | Date | undefined) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

export const formatTimestamp = (timestamp: number | undefined) => {
  if (!timestamp) return '-'
  // 处理Unix时间戳（秒级或毫秒级）
  const timestampLength = timestamp.toString().length;
  const adjustedTimestamp = timestampLength <= 10 ? timestamp * 1000 : timestamp;
  return dayjs(adjustedTimestamp).format('YYYY-MM-DD HH:mm')
}