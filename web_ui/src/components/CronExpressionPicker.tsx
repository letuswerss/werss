import React, { useState, useEffect, useMemo, useImperativeHandle, forwardRef, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Form, FormControl, FormField, FormItem, FormLabel } from '@/components/ui/form'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'

interface CronExpressionPickerProps {
  value?: string
  onChange?: (value: string) => void
}

export interface CronExpressionPickerRef {
  parseExpression: (expr: string) => void
}

const CronExpressionPicker = forwardRef<CronExpressionPickerRef, CronExpressionPickerProps>(({
  value = '* * * * *',
  onChange
}, ref) => {
  const [minutes, setMinutes] = useState('*')
  const [hours, setHours] = useState('*')
  const [days, setDays] = useState('*')
  const [months, setMonths] = useState('*')
  const [weekdays, setWeekdays] = useState('*')
  const prevValueRef = useRef<string>('')
  const isInternalUpdateRef = useRef<boolean>(false)

  const parseCronDescription = (part: string, type: string) => {
    if (part === '*') return `每${type}`
    if (part.startsWith('*/')) {
      const num = part.substring(2)
      return `每${num}${type}`
    }
    if (part.includes('-')) {
      const [start, end] = part.split('-')
      return `${start}到${end}${type}`
    }
    if (part.includes(',')) {
      return `在${part.split(',').join('、')}${type}`
    }
    return `在${part}${type}`
  }

  const cronExpression = useMemo(() => {
    return `${minutes} ${hours} ${days} ${months} ${weekdays}`
  }, [minutes, hours, days, months, weekdays])

  const cronDescription = useMemo(() => {
    const monthDesc = parseCronDescription(months, '月')
    const dayDesc = parseCronDescription(days, '日')
    const hourDesc = parseCronDescription(hours, '小时')
    const minuteDesc = parseCronDescription(minutes, '分钟')
    
    let weekdayDesc = ''
    if (weekdays === '*') {
      weekdayDesc = '每天'
    } else if (weekdays === '1-5') {
      weekdayDesc = '工作日'
    } else if (weekdays === '0,6') {
      weekdayDesc = '周末'
    } else if (weekdays.includes(',')) {
      const days = weekdays.split(',').map(d => 
        ['周日','周一','周二','周三','周四','周五','周六'][parseInt(d)]
      )
      weekdayDesc = `在${days.join('、')}`
    } else if (weekdays.includes('-')) {
      const [start, end] = weekdays.split('-').map(d => 
        ['周日','周一','周二','周三','周四','周五','周六'][parseInt(d)]
      )
      weekdayDesc = `${start}到${end}`
    } else {
      weekdayDesc = `在${['周日','周一','周二','周三','周四','周五','周六'][parseInt(weekdays)]}`
    }
    
    return `${monthDesc} ${dayDesc} ${weekdayDesc} ${hourDesc} ${minuteDesc}`
  }, [minutes, hours, days, months, weekdays])

  const updateExpression = () => {
    onChange?.(cronExpression)
  }

  const parseExpression = (expr: string) => {
    const parts = expr.split(' ')
    if (parts.length === 5) {
      // 只有当新的表达式与当前状态生成的表达式不同时才更新
      const currentExpr = `${minutes} ${hours} ${days} ${months} ${weekdays}`
      if (expr !== currentExpr) {
        isInternalUpdateRef.current = true
        setMinutes(parts[0])
        setHours(parts[1])
        setDays(parts[2])
        setMonths(parts[3])
        setWeekdays(parts[4])
        // 使用 setTimeout 确保状态更新后再重置标志
        setTimeout(() => {
          isInternalUpdateRef.current = false
        }, 0)
      }
    }
  }

  useImperativeHandle(ref, () => ({
    parseExpression
  }))

  useEffect(() => {
    if (value && value !== prevValueRef.current) {
      const currentExpr = `${minutes} ${hours} ${days} ${months} ${weekdays}`
      if (value !== currentExpr) {
        prevValueRef.current = value
        parseExpression(value)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  useEffect(() => {
    if (!isInternalUpdateRef.current) {
      if (cronExpression !== prevValueRef.current && cronExpression !== value) {
        prevValueRef.current = cronExpression
        updateExpression()
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [minutes, hours, days, months, weekdays])

  const handleExampleClick = (m: string, h: string, d: string, mon: string, w: string) => {
    setMinutes(m)
    setHours(h)
    setDays(d)
    setMonths(mon)
    setWeekdays(w)
  }

  const minuteOptions = [
    ...Array.from({ length: 60 }, (_, i) => ({ label: i.toString(), value: i.toString() })),
    { label: '*', value: '*' },
    { label: '每5分钟', value: '*/5' },
    { label: '每1-59分钟(随机)', value: '*/1~59' },
    { label: '每15分钟', value: '*/15' },
    { label: '每30分钟', value: '*/30' },
    { label: '0-30分钟', value: '0-30' },
    { label: '30-59分钟', value: '30-59' }
  ]

  const hourOptions = [
    ...Array.from({ length: 24 }, (_, i) => ({ label: i.toString(), value: i.toString() })),
    { label: '*', value: '*' },
    { label: '每1小时', value: '*/1' },
    { label: '每2小时', value: '*/2' },
    { label: '每3小时', value: '*/3' },
    { label: '每4小时', value: '*/4' },
    { label: '每5小时', value: '*/5' },
    { label: '每8小时', value: '*/8' },
    { label: '每6小时', value: '*/6' },
    { label: '每12小时', value: '*/12' },
    { label: '0-12点', value: '0-12' },
    { label: '12-23点', value: '12-23' }
  ]

  const dayOptions = [
    ...Array.from({ length: 31 }, (_, i) => ({ label: (i + 1).toString(), value: (i + 1).toString() })),
    { label: '*', value: '*' },
    { label: '每5天', value: '*/5' },
    { label: '每10天', value: '*/10' },
    { label: '1-15日', value: '1-15' },
    { label: '16-31日', value: '16-31' }
  ]

  const monthOptions = [
    ...Array.from({ length: 12 }, (_, i) => ({ label: (i + 1).toString(), value: (i + 1).toString() })),
    { label: '*', value: '*' },
    { label: '每3个月', value: '*/3' },
    { label: '每6个月', value: '*/6' },
    { label: '1-6月', value: '1-6' },
    { label: '7-12月', value: '7-12' }
  ]

  const weekdayOptions = [
    { label: '周日', value: '0' },
    { label: '周一', value: '1' },
    { label: '周二', value: '2' },
    { label: '周三', value: '3' },
    { label: '周四', value: '4' },
    { label: '周五', value: '5' },
    { label: '周六', value: '6' },
    { label: '*', value: '*' },
    { label: '工作日', value: '1-5' },
    { label: '周末', value: '0,6' },
    { label: '每隔一天', value: '*/2' }
  ]

  const examples = [
    { label: '每天午夜 (0 0 * * *)', m: '0', h: '0', d: '*', mon: '*', w: '*' },
    { label: '每天中午 (0 12 * * *)', m: '0', h: '12', d: '*', mon: '*', w: '*' },
    { label: '工作日早上9点 (0 9 * * 1-5)', m: '0', h: '9', d: '*', mon: '*', w: '1-5' },
    { label: '每5分钟 (*/5 * * * *)', m: '*/5', h: '*', d: '*', mon: '*', w: '*' },
    { label: '每6小时 (0 */6 * * *)', m: '0', h: '*/6', d: '*', mon: '*', w: '*' },
    { label: '每10天 (0 0 */10 * *)', m: '0', h: '0', d: '*/10', mon: '*', w: '*' }
  ]

  return (
    <Card className="w-full">
      <CardHeader className="flex-shrink-0">
        <CardTitle>Cron 表达式配置</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">分钟</label>
            <Select value={minutes} onValueChange={(value) => setMinutes(value)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
            {minuteOptions.map(opt => (
                  <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
                  </SelectItem>
            ))}
              </SelectContent>
          </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">小时</label>
            <Select value={hours} onValueChange={(value) => setHours(value)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
            {hourOptions.map(opt => (
                  <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
                  </SelectItem>
            ))}
              </SelectContent>
          </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">日</label>
            <Select value={days} onValueChange={(value) => setDays(value)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
            {dayOptions.map(opt => (
                  <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
                  </SelectItem>
            ))}
              </SelectContent>
          </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">月</label>
            <Select value={months} onValueChange={(value) => setMonths(value)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
            {monthOptions.map(opt => (
                  <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
                  </SelectItem>
            ))}
              </SelectContent>
          </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">星期</label>
            <Select value={weekdays} onValueChange={(value) => setWeekdays(value)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
            {weekdayOptions.map(opt => (
                  <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
                  </SelectItem>
            ))}
              </SelectContent>
          </Select>
          </div>
        </div>

        <Separator />

        <div className="space-y-2">
          <p className="text-sm font-semibold">表达式预览: {cronExpression}</p>
          <p className="text-sm text-muted-foreground">解释: {cronDescription}</p>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-semibold">常用示例:</p>
          <div className="space-y-1">
            {examples.map((item, index) => (
              <div
                key={index}
                className="py-2 px-3 cursor-pointer rounded-md text-primary hover:bg-accent transition-colors"
                onClick={() => handleExampleClick(item.m, item.h, item.d, item.mon, item.w)}
              >
                {item.label}
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
})

CronExpressionPicker.displayName = 'CronExpressionPicker'

export default CronExpressionPicker
