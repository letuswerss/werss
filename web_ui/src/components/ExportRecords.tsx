import { useState, useEffect, useImperativeHandle, forwardRef } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Pagination, PaginationContent, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from '@/components/ui/pagination'
import { useToast } from '@/hooks/use-toast'
import { Modal } from '@/utils/modal'
import { getExportRecords, DeleteExportRecords } from '@/api/tools'
import { Download, Trash2, Loader2 } from 'lucide-react'

interface ExportRecord {
  filename: string
  size: number | string
  created_time: string | number
  modified_time?: string | number
  download_url: string
  path?: string
}

interface ExportRecordsProps {
  mp_id?: string
}

export interface ExportRecordsRef {
  fetchExportRecords: () => Promise<void>
}

const ExportRecords = forwardRef<ExportRecordsRef, ExportRecordsProps>(({ mp_id = '' }, ref) => {
  const [loading, setLoading] = useState(false)
  const [exportRecords, setExportRecords] = useState<ExportRecord[]>([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })
  const { toast } = useToast()

  const formatFileSize = (size: number | string): string => {
    try {
      const sizeInBytes = typeof size === 'string' ? parseInt(size) : size
      if (isNaN(sizeInBytes) || sizeInBytes <= 0) {
        return '0 MB'
      }
      const sizeInMB = sizeInBytes / (1024 * 1024)
      return `${sizeInMB.toFixed(2)} MB`
    } catch (error) {
      return '0 MB'
    }
  }

  const formatDateTime = (dateTime: string | number): string => {
    if (!dateTime) return '-'

    try {
      const date = new Date(dateTime)
      if (isNaN(date.getTime())) return '-'

      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    } catch (error) {
      return '-'
    }
  }

  const handleDownload = (record: ExportRecord) => {
    if (record.download_url && record.download_url !== '#') {
      window.open(record.download_url, '_blank')
    } else {
      toast({
        variant: "destructive",
        title: "错误",
        description: '下载链接不可用'
      })
    }
  }

  const handleDelete = async (record: ExportRecord) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除文件 "${record.filename}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response: any = await DeleteExportRecords({
            mp_id: mp_id,
            filename: record.path || record.filename
          })
          console.log('删除API返回数据:', response)
          if (response?.message && response.message.indexOf('成功') !== -1) {
            const index = exportRecords.findIndex((item) => item.filename === record.filename)
            if (index > -1) {
              const newRecords = [...exportRecords]
              newRecords.splice(index, 1)
              setExportRecords(newRecords)
              toast({
                title: "成功",
                description: '删除成功'
              })
            }
          } else {
            toast({
              variant: "destructive",
              title: "删除失败",
              description: response.data?.message || '未知错误'
            })
          }
        } catch (error) {
          console.error('删除导出记录失败:', error)
        }
      }
    })
  }

  const fetchExportRecords = async (): Promise<void> => {
    setLoading(true)
    try {
      const response: any = await getExportRecords({ mp_id })
      console.log('API 返回数据:', response)
      const records = Array.isArray(response) ? response : (response?.data || [])
      const formattedRecords = records.map((record: any) => ({
        ...record,
        filename: record.filename || '-',
        size: record.size || 0,
        created_time: record.created_time || '-',
        modified_time: record.modified_time || '-',
        download_url: record.download_url || '#'
      }))
      setExportRecords(formattedRecords)
      setPagination(prev => ({ ...prev, total: formattedRecords.length }))
      console.log('表格数据:', formattedRecords)
    } catch (error) {
      console.error('获取导出记录失败:', error)
      setExportRecords([])
    } finally {
      setLoading(false)
    }
  }

  useImperativeHandle(ref, () => ({
    fetchExportRecords
  }))

  useEffect(() => {
    fetchExportRecords()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mp_id])

  const startIndex = (pagination.current - 1) * pagination.pageSize
  const endIndex = startIndex + pagination.pageSize
  const paginatedRecords = exportRecords.slice(startIndex, endIndex)
  const totalPages = Math.ceil(pagination.total / pagination.pageSize)

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 text-foreground">
          导出记录
        </h1>
        <p className="text-muted-foreground text-sm">查看和管理导出的文件</p>
      </div>
      <Card className="rounded-lg shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between">
          <h2 className="text-lg font-semibold">导出文件列表</h2>
          <Button 
            onClick={fetchExportRecords}
          >
            刷新
          </Button>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center items-center py-10">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>文件名</TableHead>
                    <TableHead>文件大小</TableHead>
                    <TableHead>创建时间</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedRecords.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-muted-foreground py-10">
                        暂无数据
                      </TableCell>
                    </TableRow>
                  ) : (
                    paginatedRecords.map((record, index) => (
                      <TableRow key={record.filename || index}>
                        <TableCell>{record.filename}</TableCell>
                        <TableCell>{formatFileSize(record.size)}</TableCell>
                        <TableCell>{formatDateTime(record.created_time)}</TableCell>
                        <TableCell>
                          <div className="flex gap-2 items-center">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDownload(record)}
                            >
                              <Download className="h-4 w-4 mr-2" />
                              下载
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDelete(record)}
                              className="text-destructive hover:text-destructive"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              删除
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
              {totalPages > 1 && (
                <Pagination className="mt-4">
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious 
                        onClick={() => setPagination(prev => ({ ...prev, current: Math.max(1, prev.current - 1) }))}
                        className={pagination.current === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                      />
                    </PaginationItem>
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                      <PaginationItem key={page}>
                        <PaginationLink
                          onClick={() => setPagination(prev => ({ ...prev, current: page }))}
                          isActive={pagination.current === page}
                          className="cursor-pointer"
                        >
                          {page}
                        </PaginationLink>
                      </PaginationItem>
                    ))}
                    <PaginationItem>
                      <PaginationNext 
                        onClick={() => setPagination(prev => ({ ...prev, current: Math.min(totalPages, prev.current + 1) }))}
                        className={pagination.current === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                      />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
})

ExportRecords.displayName = 'ExportRecords'

export default ExportRecords
