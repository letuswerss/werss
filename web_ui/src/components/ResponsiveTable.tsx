import React, { useMemo } from 'react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'

interface ResponsiveTableProps {
  columns: Array<{
    title: string
    dataIndex?: string
    key?: string
    render?: (value: any, record: any, index: number) => React.ReactNode
    width?: string | number
    ellipsis?: boolean
  }>
  data: any[]
  loading?: boolean
  pagination?: {
    current?: number
    pageSize?: number
    total?: number
    onChange?: (page: number, pageSize: number) => void
  }
  rowSelection?: {
    selectedRowKeys?: (string | number)[]
    onChange?: (keys: (string | number)[]) => void
  }
  rowKey?: string | ((record: any) => string | number)
  onPageChange?: (page: number, pageSize: number) => void
  children?: React.ReactNode
}

const ResponsiveTable: React.FC<ResponsiveTableProps> = ({
  columns,
  data,
  loading = false,
  pagination,
  rowSelection,
  rowKey = 'id',
  onPageChange,
  children
}) => {
  const width = typeof window !== 'undefined' ? window.innerWidth : 1024
  const isMobile = useMemo(() => width < 768, [width])

  const getRowKey = (record: any, index: number): string | number => {
    if (typeof rowKey === 'function') {
      return rowKey(record)
    }
    return record[rowKey] ?? index
  }

  const handlePageChange = (page: number, pageSize: number) => {
    onPageChange?.(page, pageSize)
    pagination?.onChange?.(page, pageSize)
  }

  return (
    <div>
      <div className="border">
        <Table>
          <TableHeader>
            <TableRow>
              {rowSelection && (
                <TableHead className="w-12">
                  <input
                    type="checkbox"
                    checked={
                      data.length > 0 &&
                      data.every((record, index) =>
                        rowSelection.selectedRowKeys?.includes(getRowKey(record, index))
                      )
                    }
                    onChange={(e) => {
                      if (e.target.checked) {
                        rowSelection.onChange?.(data.map((record, index) => getRowKey(record, index)))
                      } else {
                        rowSelection.onChange?.([])
                      }
                    }}
                  />
                </TableHead>
              )}
              {columns.map((column, index) => (
                <TableHead
                  key={column.key || column.dataIndex || index}
                  style={column.width ? { width: column.width } : undefined}
                  className={column.ellipsis ? 'truncate' : ''}
                >
                  {column.title}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={columns.length + (rowSelection ? 1 : 0)} className="h-24 text-center">
                  加载中...
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length + (rowSelection ? 1 : 0)} className="h-24 text-center">
                  暂无数据
                </TableCell>
              </TableRow>
            ) : (
              data.map((record, recordIndex) => {
                const key = getRowKey(record, recordIndex)
                return (
                  <TableRow key={key}>
                    {rowSelection && (
                      <TableCell>
                        <input
                          title="选择"
                          type="checkbox"
                          checked={rowSelection.selectedRowKeys?.includes(key) ?? false}
                          onChange={(e) => {
                            const currentKeys = rowSelection.selectedRowKeys || []
                            if (e.target.checked) {
                              rowSelection.onChange?.([...currentKeys, key])
                            } else {
                              rowSelection.onChange?.(currentKeys.filter((k) => k !== key))
                            }
                          }}
                        />
                      </TableCell>
                    )}
                    {columns.map((column, colIndex) => {
                      const value = column.dataIndex ? record[column.dataIndex] : undefined
                      const content = column.render
                        ? column.render(value, record, recordIndex)
                        : value
                      return (
                        <TableCell
                          key={column.key || column.dataIndex || colIndex}
                          className={column.ellipsis ? 'truncate' : ''}
                        >
                          {content}
                        </TableCell>
                      )
                    })}
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>
      {pagination && pagination.total && pagination.total > 0 && (
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            共 {pagination.total} 条，第 {pagination.current || 1} / {Math.ceil((pagination.total || 0) / (pagination.pageSize || 10))} 页
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(Math.max(1, (pagination.current || 1) - 1), pagination.pageSize || 10)}
              disabled={(pagination.current || 1) === 1}
            >
              上一页
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(Math.min(Math.ceil((pagination.total || 0) / (pagination.pageSize || 10)), (pagination.current || 1) + 1), pagination.pageSize || 10)}
              disabled={(pagination.current || 1) >= Math.ceil((pagination.total || 0) / (pagination.pageSize || 10))}
            >
              下一页
            </Button>
          </div>
        </div>
      )}
      {children}
    </div>
  )
}

export default ResponsiveTable
