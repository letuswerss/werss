import React from 'react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'
import type { MessageTask } from '@/types/messageTask'

interface TaskListProps {
  taskList: MessageTask[]
  loading: boolean
  pagination: {
    current?: number
    pageSize?: number
    total?: number
  }
  isMobile: boolean
  onPageChange?: (page: number) => void
  onLoadMore?: () => void
  onEdit?: (id: number) => void
  onTest?: (id: number) => void
  onRun?: (id: number) => void
  onDelete?: (id: number) => void
  actions?: (record: MessageTask) => React.ReactNode
  mobileActions?: (record: MessageTask) => React.ReactNode
}

const TaskList: React.FC<TaskListProps> = ({
  taskList,
  loading,
  pagination,
  isMobile,
  onPageChange,
  onLoadMore,
  actions,
  mobileActions
}) => {
  const parseCronExpression = (exp: string) => {
    const parts = exp.split(' ')
    if (parts.length !== 5) return exp
    
    const [minute, hour, day, month, week] = parts
    
    let result = ''
    
    // 解析分钟
    if (minute === '*') {
      result += '每分钟'
    } else if (minute.includes('/')) {
      const [, interval] = minute.split('/')
      result += `每${interval}分钟`
    } else {
      result += `在${minute}分`
    }
    
    // 解析小时
    if (hour === '*') {
      result += '每小时'
    } else if (hour.includes('/')) {
      const [, interval] = hour.split('/')
      result += `每${interval}小时`
    } else {
      result += ` ${hour}时`
    }
    
    // 解析日期
    if (day === '*') {
      result += ' 每天'
    } else if (day.includes('/')) {
      const [, interval] = day.split('/')
      result += ` 每${interval}天`
    } else {
      result += ` ${day}日`
    }
    
    // 解析月份
    if (month === '*') {
      result += ' 每月'
    } else if (month.includes('/')) {
      const [, interval] = month.split('/')
      result += ` 每${interval}个月`
    } else {
      result += ` ${month}月`
    }
    
    // 解析星期
    if (week !== '*') {
      result += ` 星期${week}`
    }
    
    return result || exp
  }

  if (!isMobile) {
    const totalPages = pagination.total && pagination.pageSize 
      ? Math.ceil(pagination.total / pagination.pageSize) 
      : 0
    const currentPage = pagination.current || 1

    return (
      <div className="space-y-4">
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[200px]">名称</TableHead>
                <TableHead>cron表达式</TableHead>
                <TableHead className="w-[100px]">类型</TableHead>
                <TableHead className="w-[100px]">状态</TableHead>
                <TableHead className="w-[260px]">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                  </TableRow>
                ))
              ) : taskList.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    暂无数据
                  </TableCell>
                </TableRow>
              ) : (
                taskList.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell className="font-medium truncate max-w-[200px]">
                      {record.name}
                    </TableCell>
                    <TableCell>{parseCronExpression(record.cron_exp || '')}</TableCell>
                    <TableCell>
                      <Badge variant={record.message_type === 1 ? 'default' : 'destructive'}>
                        {record.message_type === 1 ? 'WeekHook' : 'Message'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={record.status === 1 ? 'default' : 'destructive'}>
                        {record.status === 1 ? '启用' : '禁用'}
                      </Badge>
                    </TableCell>
                    <TableCell>{actions?.(record)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
        {totalPages > 1 && (
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious 
                  href="#"
                  onClick={(e) => {
                    e.preventDefault()
                    if (currentPage > 1 && onPageChange) {
                      onPageChange(currentPage - 1)
                    }
                  }}
                  className={currentPage <= 1 ? 'pointer-events-none opacity-50' : ''}
                />
              </PaginationItem>
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                let pageNum: number
                if (totalPages <= 5) {
                  pageNum = i + 1
                } else if (currentPage <= 3) {
                  pageNum = i + 1
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i
                } else {
                  pageNum = currentPage - 2 + i
                }
                return (
                  <PaginationItem key={pageNum}>
                    <PaginationLink
                      href="#"
                      onClick={(e) => {
                        e.preventDefault()
                        if (onPageChange) {
                          onPageChange(pageNum)
                        }
                      }}
                      isActive={currentPage === pageNum}
                    >
                      {pageNum}
                    </PaginationLink>
                  </PaginationItem>
                )
              })}
              <PaginationItem>
                <PaginationNext
                  href="#"
                  onClick={(e) => {
                    e.preventDefault()
                    if (currentPage < totalPages && onPageChange) {
                      onPageChange(currentPage + 1)
          }
        }}
                  className={currentPage >= totalPages ? 'pointer-events-none opacity-50' : ''}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {loading ? (
        Array.from({ length: 5 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-3/4" />
            </CardContent>
          </Card>
        ))
      ) : (
        taskList.map((item) => (
          <Card key={item.id}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1 space-y-2">
                  <h3 className="font-semibold">{item.name}</h3>
                  <div className="text-sm text-muted-foreground">
                    {parseCronExpression(item.cron_exp || '')}
                  </div>
                  <div className="flex gap-2">
                    <Badge variant={item.message_type === 1 ? 'default' : 'destructive'}>
                    {item.message_type === 1 ? 'WeekHook' : 'Message'}
                    </Badge>
                    <Badge variant={item.status === 1 ? 'default' : 'destructive'}>
                    {item.status === 1 ? '启用' : '禁用'}
                    </Badge>
                  </div>
                </div>
                {mobileActions?.(item)}
              </div>
            </CardContent>
          </Card>
        ))
      )}
      {pagination.current && pagination.pageSize && pagination.total &&
        pagination.current * pagination.pageSize < pagination.total && (
          <div className="w-[120px] mx-auto text-center space-y-2">
            <Button
              variant="default"
              className="w-full"
              disabled={loading}
              onClick={onLoadMore}
            >
              {loading ? '加载中...' : '加载更多'}
            </Button>
            <div className="text-muted-foreground text-sm">
              共 {pagination.total} 条
            </div>
          </div>
        )}
    </div>
  )
}

export default TaskList
