import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Message } from '@/utils/message'
import { Plus, Edit, Trash2, Copy, RefreshCw, Search, Loader2, Eye, EyeOff, Key } from 'lucide-react'
import { useForm } from 'react-hook-form'
import {
  getApiKeys,
  createApiKey,
  updateApiKey,
  deleteApiKey,
  getApiKeyLogs,
  regenerateApiKey
} from '@/api/apiKey'
import type {
  ApiKey,
  ApiKeyLog,
  ApiKeyListResponse,
  ApiKeyLogListResponse,
  CreateApiKeyParams,
  UpdateApiKeyParams
} from '@/types/apiKey'
import { formatDateTime } from '@/utils/date'
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useTranslation } from 'react-i18next'

// 权限选项列表
const PERMISSION_OPTIONS = [
  { value: 'read', label: '读' },
  { value: 'read_write', label: '读写' },
]

const ApiKeyManagement: React.FC = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [selectedApiKey, setSelectedApiKey] = useState<ApiKey | null>(null)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })
  const [searchText, setSearchText] = useState('')
  const [visible, setVisible] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null)
  const [regenerateDialogOpen, setRegenerateDialogOpen] = useState(false)
  const [regenerateTargetId, setRegenerateTargetId] = useState<string | null>(null)
  const [newApiKey, setNewApiKey] = useState<string | null>(null)
  const [newApiKeyId, setNewApiKeyId] = useState<string | null>(null) // 存储新创建的 API Key ID
  
  // 从 localStorage 加载已保存的 API Key
  const loadApiKeyMapFromStorage = (): Record<string, string> => {
    try {
      const stored = localStorage.getItem('apiKeyMap')
      return stored ? JSON.parse(stored) : {}
    } catch {
      return {}
    }
  }
  
  const [apiKeyMap, setApiKeyMap] = useState<Record<string, string>>(loadApiKeyMapFromStorage())
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({})
  
  // 保存 API Key 到 localStorage
  const saveApiKeyToStorage = (id: string, key: string) => {
    setApiKeyMap(prev => {
      const updated = { ...prev, [id]: key }
      try {
        localStorage.setItem('apiKeyMap', JSON.stringify(updated))
      } catch (error) {
        console.error('保存 API Key 到 localStorage 失败:', error)
      }
      return updated
    })
  }
  const [logs, setLogs] = useState<ApiKeyLog[]>([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [logsPagination, setLogsPagination] = useState({
    current: 1,
    pageSize: 10, // 日志每页显示条数
    total: 0
  })

  const form = useForm<CreateApiKeyParams & UpdateApiKeyParams>({
    defaultValues: {
      name: '',
      permissions: null,
      is_active: true
    }
  })

  // 加载 API Key 列表
  const loadApiKeys = async () => {
    setLoading(true)
    try {
      const res = await getApiKeys({
        page: pagination.current,
        pageSize: pagination.pageSize
      }) as unknown as ApiKeyListResponse

      const list = res.list || []
      const total = res.total || 0

      // 过滤搜索文本
      const filteredList = searchText
        ? list.filter((key: ApiKey) => key.name.toLowerCase().includes(searchText.toLowerCase()))
        : list

      setApiKeys(filteredList)
      setPagination(prev => ({ ...prev, total: searchText ? filteredList.length : total }))
    } catch (error: any) {
      console.error('获取 API Key 列表失败:', error)
      Message.error(error.message || t('apiKeys.messages.fetchFailed'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadApiKeys()
  }, [pagination.current, pagination.pageSize])

  useEffect(() => {
    const timer = setTimeout(() => {
      if (pagination.current === 1) {
        loadApiKeys()
      } else {
        setPagination(prev => ({ ...prev, current: 1 }))
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [searchText])

  // 加载使用日志
  const loadLogs = async (apiKeyId: string) => {
    if (!apiKeyId) return
    setLogsLoading(true)
    try {
      const res = await getApiKeyLogs(apiKeyId, {
        page: logsPagination.current,
        pageSize: logsPagination.pageSize
      }) as unknown as ApiKeyLogListResponse

      const list = res.list || []
      const total = res.total || 0

      setLogs(list)
      setLogsPagination(prev => ({ ...prev, total }))
    } catch (error: any) {
      console.error('获取使用日志失败:', error)
      Message.error(error.message || t('apiKeys.messages.fetchLogsFailed'))
    } finally {
      setLogsLoading(false)
    }
  }

  // 选择 API Key
  const handleSelectApiKey = (apiKey: ApiKey) => {
    const savedKey = apiKeyMap[apiKey.id]
    const apiKeyWithSavedKey = savedKey ? { ...apiKey, key: savedKey } : apiKey
    setSelectedApiKey(apiKeyWithSavedKey)
    setLogsPagination(prev => ({ ...prev, current: 1 }))
    loadLogs(apiKey.id)
  }

  // 创建 API Key
  const handleCreate = () => {
    setIsEditing(false)
    form.reset({
      name: '',
      permissions: null,
      is_active: true
    })
    setVisible(true)
  }

  // 编辑 API Key
  const handleEdit = (apiKey: ApiKey) => {
    setIsEditing(true)
    form.reset({
      name: apiKey.name,
      permissions: apiKey.permissions || null,
      is_active: apiKey.is_active
    })
    setSelectedApiKey(apiKey)
    setVisible(true)
  }

  // 保存 API Key
  const handleSave = async () => {
    try {
      const values = form.getValues()
      const submitData = {
        ...values,
        permissions: values.permissions || null
      }
      
      if (isEditing && selectedApiKey) {
        await updateApiKey(selectedApiKey.id, submitData)
        Message.success(t('apiKeys.messages.updateSuccess'))
      } else {
        const res = await createApiKey(submitData)
        const newKey = (res as any)?.data?.key || (res as any)?.key
        const newKeyId = (res as any)?.data?.id || (res as any)?.id
        if (newKey && newKeyId) {
          setNewApiKey(newKey)
          setNewApiKeyId(newKeyId)
          saveApiKeyToStorage(newKeyId, newKey)
          Message.success(t('apiKeys.messages.createSuccess'))
        } else {
          Message.success(t('apiKeys.messages.createSuccessSimple'))
        }
      }
      setVisible(false)
      await loadApiKeys()
      
      if (!isEditing && newApiKeyId) {
        setTimeout(() => {
          const newKey = apiKeys.find(k => k.id === newApiKeyId)
          if (newKey) {
            setSelectedApiKey({ ...newKey, key: apiKeyMap[newApiKeyId] })
            setShowApiKey(prev => ({ ...prev, [newApiKeyId]: true }))
          }
        }, 100)
      }
      if (selectedApiKey && isEditing) {
        const updated = apiKeys.find(k => k.id === selectedApiKey.id)
        if (updated) {
          setSelectedApiKey(updated)
        }
      }
    } catch (error: any) {
      console.error('保存 API Key 失败:', error)
      const errorMessage = error?.response?.data?.detail?.message || 
                          error?.response?.data?.message || 
                          error?.message || 
                          '保存失败'
      Message.error(errorMessage)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteApiKey(id)
      Message.success(t('apiKeys.messages.deleteSuccess'))
      if (selectedApiKey?.id === id) {
        setSelectedApiKey(null)
        setLogs([])
      }
      loadApiKeys()
    } catch (error: any) {
      Message.error(error.message || t('apiKeys.messages.deleteFailed'))
    }
  }

  const handleRegenerate = async (id: string) => {
    try {
      const res = await regenerateApiKey(id)
      const newKey = (res as any)?.data?.key || (res as any)?.key
      if (newKey) {
        setNewApiKey(newKey)
        setNewApiKeyId(id)
        saveApiKeyToStorage(id, newKey)
        Message.success(t('apiKeys.messages.regenerateSuccess'))
      } else {
        Message.success(t('apiKeys.messages.regenerateSuccessSimple'))
      }
      setRegenerateDialogOpen(false)
      setRegenerateTargetId(null)
      loadApiKeys()
      if (selectedApiKey?.id === id) {
        setSelectedApiKey(prev => prev ? { ...prev, key: newKey } : null)
      }
    } catch (error: any) {
      Message.error(error.message || t('apiKeys.messages.regenerateFailed'))
    }
  }

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      Message.success(t('apiKeys.messages.copySuccess'))
    } catch (error) {
      Message.error(t('apiKeys.messages.copyFailed'))
    }
  }

  const toggleShowApiKey = (id: string) => {
    setShowApiKey(prev => ({ ...prev, [id]: !prev[id] }))
  }

  const totalPages = Math.ceil(pagination.total / pagination.pageSize)
  const logTotalPages = Math.ceil(logsPagination.total / logsPagination.pageSize)

  return (
    // 使用 h-screen 和 flex flex-col 确保布局占满全屏，防止出现双滚动条
    <div className="h-screen w-full flex flex-col overflow-hidden">
      
      {/* 头部标题区：固定高度 */}
      <div className="flex-shrink-0 p-6 pb-4">
        <h1 className="text-3xl font-bold mb-2 text-foreground">
          API Key 管理
        </h1>
        <p className="text-muted-foreground text-sm">
          管理和查看您的 API Key，支持权限绑定和使用日志记录
        </p>
      </div>

      {/* 主内容区域：flex-1 自动填充剩余高度，min-h-0 防止子元素溢出 */}
      <div className="flex-1 min-h-0 flex gap-6 px-6 pb-6">
        
        {/* 左侧：API Key 列表 */}
        <div className="w-[420px] rounded-lg border bg-white shadow-sm dark:bg-background flex flex-col flex-shrink-0 overflow-hidden">
          {/* 搜索区域 */}
          <div className="p-4 border-b flex-shrink-0">
            <div className="flex gap-3 mb-3">
              <div className="relative flex-1">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="搜索 API Key 名称..."
                  value={searchText}
                  onChange={(e) => {
                    setSearchText(e.target.value)
                    setPagination(prev => ({ ...prev, current: 1 }))
                  }}
                  className="pl-8"
                />
              </div>
            </div>
            <Button className="w-full" onClick={handleCreate}>
              <Plus className="h-4 w-4 mr-2" />
              创建 API Key
            </Button>
          </div>

          {/* 列表区域：使用 flex-1 撑开 */}
          <div className="flex-1 overflow-auto p-2">
            <div className="rounded-md border overflow-hidden bg-card">
              <Table>
                <TableHeader className="sticky top-0 z-10 bg-card shadow-sm">
                  <TableRow>
                    <TableHead>名称</TableHead>
                    <TableHead className="text-center">状态</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={2} className="h-24 text-center">
                        <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                      </TableCell>
                    </TableRow>
                  ) : apiKeys.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={2} className="h-24 text-center text-muted-foreground">
                        暂无数据
                      </TableCell>
                    </TableRow>
                  ) : (
                    apiKeys.map((record) => (
                      <TableRow
                        key={record.id}
                        className={`cursor-pointer transition-all ${
                          selectedApiKey?.id === record.id
                            ? 'bg-primary/10 border-l-4 border-l-primary'
                            : 'hover:bg-muted/50'
                        }`}
                        onClick={() => handleSelectApiKey(record)}
                      >
                        <TableCell className="font-medium py-3">
                          {record.name}
                        </TableCell>
                        <TableCell className="text-center py-3">
                          <Badge variant={record.is_active ? 'default' : 'destructive'} className="rounded px-2">
                            <span className="dark:text-dark text-xs">{record.is_active ? '启用' : '禁用'}</span>
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
            {/* 左侧分页 */}
            {totalPages > 1 && (
              <div className="mt-4 pb-2 px-1">
                <Pagination>
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious
                        href="#"
                        onClick={(e) => {
                          e.preventDefault()
                          if (pagination.current > 1) {
                            setPagination(prev => ({ ...prev, current: prev.current - 1 }))
                          }
                        }}
                        className={pagination.current <= 1 ? 'pointer-events-none opacity-50' : ''}
                      />
                    </PaginationItem>
                    <PaginationItem>
                         <span className="text-xs text-muted-foreground px-2">{pagination.current} / {totalPages}</span>
                        </PaginationItem>
                    <PaginationItem>
                      <PaginationNext
                        href="#"
                        onClick={(e) => {
                          e.preventDefault()
                          if (pagination.current < totalPages) {
                            setPagination(prev => ({ ...prev, current: prev.current + 1 }))
                          }
                        }}
                        className={pagination.current >= totalPages ? 'pointer-events-none opacity-50' : ''}
                      />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              </div>
            )}
          </div>
        </div>

        {/* 右侧：API Key 详情 */}
        <div className="flex-1 min-w-[500px] flex flex-col h-full overflow-hidden">
          {selectedApiKey ? (
            <Card className="rounded-lg border bg-white shadow-sm dark:bg-background flex flex-col h-full overflow-hidden">
              <CardHeader className="flex-shrink-0 pb-4 pt-6 px-6 border-b">
                <div className="flex md:flex-row flex-col items-center gap-4 w-full">
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Key className="h-6 w-6 text-primary" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-lg font-bold text-foreground mb-1 truncate">
                        {selectedApiKey.name}
                      </div>
                      <div className="text-xs text-muted-foreground truncate font-mono select-all">
                        {selectedApiKey.id}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    <Button variant="outline" size="sm" onClick={() => handleEdit(selectedApiKey)}>
                      <Edit className="h-3.5 w-3.5 mr-2" />
                      编辑
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setRegenerateTargetId(selectedApiKey.id)
                        setRegenerateDialogOpen(true)
                      }}
                    >
                      <RefreshCw className="h-3.5 w-3.5 mr-2" />
                      重置
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => {
                        setDeleteTargetId(selectedApiKey.id)
                        setDeleteDialogOpen(true)
                      }}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              </CardHeader>

              {/* 使用 flex-1 和 p-0 让 Tabs 接管剩余空间 */}
              <CardContent className="flex-1 overflow-hidden p-0 flex flex-col min-h-0">
                <Tabs defaultValue="details" className="flex flex-col h-full w-full">
                  <div className="px-6 pt-4 border-b flex-shrink-0">
                  <TabsList className="w-fit">
                      <TabsTrigger value="details">详情信息</TabsTrigger>
                      <TabsTrigger value="logs">调用日志</TabsTrigger>
                  </TabsList>
                      </div>
                  
                  {/* 详情 Tab：允许自身滚动 */}
                  <TabsContent value="details" className="flex-1 overflow-y-auto p-6 space-y-6 m-0">
                      {/* API Key 值 */}
                      <div className="space-y-2 rounded-lg border bg-white p-4 dark:bg-muted/30">
                        <div className="text-sm font-semibold text-muted-foreground">API Key 密钥</div>
                      <div className="flex items-center gap-2">
                          <code className="flex-1 rounded border bg-white px-3 py-2 text-sm font-mono break-all shadow-sm dark:bg-background">
                          {showApiKey[selectedApiKey.id] 
                              ? (selectedApiKey.key || apiKeyMap[selectedApiKey.id] || '密钥不可用') 
                              : '••••••••••••••••••••••••••••••••'}
                        </code>
                          <div className="flex gap-1">
                            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => toggleShowApiKey(selectedApiKey.id)}>
                              {showApiKey[selectedApiKey.id] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                        <Button
                              variant="ghost" 
                              size="icon"
                              className="h-8 w-8"
                              disabled={!selectedApiKey.key && !apiKeyMap[selectedApiKey.id]}
                          onClick={() => {
                                const k = selectedApiKey.key || apiKeyMap[selectedApiKey.id]
                                if(k) handleCopy(k)
                              }}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                      </div>

                      {/* 状态与权限 */}
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2 rounded-lg border bg-white p-4 dark:bg-muted/30">
                          <div className="text-xs font-semibold text-muted-foreground">当前状态</div>
                          <Badge variant={selectedApiKey.is_active ? 'default' : 'destructive'} className="text-sm px-3 py-1">
                            {selectedApiKey.is_active ? '已启用' : '已禁用'}
                        </Badge>
                      </div>
                        <div className="space-y-2 rounded-lg border bg-white p-4 dark:bg-muted/30">
                          <div className="text-xs font-semibold text-muted-foreground">权限范围</div>
                          <div>
                           {selectedApiKey.permissions === 'read' && <Badge variant="secondary">Read Only</Badge>}
                           {selectedApiKey.permissions === 'read_write' && <Badge variant="secondary">Read / Write</Badge>}
                           {!selectedApiKey.permissions && <span className="text-sm text-muted-foreground">-</span>}
                    </div>
                      </div>
                    </div>

                      {/* 时间信息 */}
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2 rounded-lg border bg-white p-4 dark:bg-muted/30">
                          <div className="text-xs font-semibold text-muted-foreground">创建时间</div>
                          <div className="text-sm font-mono text-foreground">{formatDateTime(selectedApiKey.created_at)}</div>
                      </div>
                        <div className="space-y-2 rounded-lg border bg-white p-4 dark:bg-muted/30">
                          <div className="text-xs font-semibold text-muted-foreground">最后使用</div>
                          <div className="text-sm font-mono text-foreground">
                            {selectedApiKey.last_used_at ? formatDateTime(selectedApiKey.last_used_at) : '暂无调用记录'}
                      </div>
                      </div>
                    </div>
                  </TabsContent>

                  {/* 日志 Tab：核心修复区域，确保表格区域自适应高度且分页固定底部 */}
                  <TabsContent value="logs" className="flex-1 flex flex-col min-h-0 overflow-hidden m-0 p-0">
                    <div className="flex-1 overflow-hidden flex flex-col relative p-6 pb-2 min-h-0">
                      <div className="flex flex-1 flex-col min-h-0 overflow-hidden rounded-lg border border-border bg-card shadow-sm">
                        <div className="min-h-0 flex-1 overflow-auto">
                        <Table>
                          <TableHeader className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm shadow-sm supports-[backdrop-filter]:bg-card/80">
                            <TableRow>
                              <TableHead className="w-[170px]">调用时间</TableHead>
                              <TableHead>接口地址</TableHead>
                              <TableHead className="w-[80px]">方法</TableHead>
                              <TableHead className="w-[120px]">来源 IP</TableHead>
                              <TableHead className="text-center w-[80px]">状态码</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {logsLoading ? (
                              <TableRow><TableCell colSpan={5} className="h-32 text-center"><Loader2 className="animate-spin h-6 w-6 mx-auto"/></TableCell></TableRow>
                            ) : logs.length === 0 ? (
                              <TableRow><TableCell colSpan={5} className="h-32 text-center text-muted-foreground">暂无日志数据</TableCell></TableRow>
                            ) : (
                              logs.map((log) => (
                                <TableRow key={log.id} className="hover:bg-muted/50">
                                  <TableCell className="text-xs font-mono whitespace-nowrap text-muted-foreground">
                                    {formatDateTime(log.created_at)}
                                  </TableCell>
                                  <TableCell className="text-xs font-mono max-w-[180px] truncate" title={log.endpoint}>
                                    {log.endpoint}
                                  </TableCell>
                                  <TableCell>
                                    <Badge variant="outline" className="text-[10px] px-1 font-bold">{log.method}</Badge>
                                  </TableCell>
                                  <TableCell className="text-xs text-muted-foreground">{log.ip_address}</TableCell>
                                  <TableCell className="text-center">
                                    <Badge
                                      variant={log.status_code < 300 ? 'outline' : 'destructive'} 
                                      className={`text-[10px] ${log.status_code < 300 ? 'text-green-600 border-green-200 bg-green-50' : ''}`}
                                    >
                                      {log.status_code}
                                    </Badge>
                                  </TableCell>
                                </TableRow>
                              ))
                            )}
                          </TableBody>
                        </Table>
                        </div>
                      </div>
                    </div>
                    
                    {/* 日志分页：固定在底部，flex-shrink-0 确保不被挤压 */}
                    {logTotalPages > 0 && (
                      <div className="border-t bg-card px-6 py-3 flex-shrink-0">
                        <Pagination>
                          <PaginationContent>
                            <PaginationItem>
                              <PaginationPrevious
                                href="#"
                                onClick={(e) => {
                                  e.preventDefault()
                                  if (logsPagination.current > 1) {
                                    setLogsPagination(prev => ({ ...prev, current: prev.current - 1 }))
                                    loadLogs(selectedApiKey.id)
                                  }
                                }}
                                className={logsPagination.current <= 1 ? 'pointer-events-none opacity-50' : ''}
                              />
                            </PaginationItem>
                            <PaginationItem>
                              <span className="text-xs text-muted-foreground px-4">
                                页码 {logsPagination.current} / {logTotalPages}
                              </span>
                            </PaginationItem>
                            <PaginationItem>
                              <PaginationNext
                                href="#"
                                onClick={(e) => {
                                  e.preventDefault()
                                  if (logsPagination.current < logTotalPages) {
                                    setLogsPagination(prev => ({ ...prev, current: prev.current + 1 }))
                                    loadLogs(selectedApiKey.id)
                                  }
                                }}
                                className={logsPagination.current >= logTotalPages ? 'pointer-events-none opacity-50' : ''}
                              />
                            </PaginationItem>
                          </PaginationContent>
                        </Pagination>
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ) : (
            <Card className="h-full flex items-center justify-center border-dashed bg-white dark:bg-muted/10">
              <div className="text-center space-y-3">
                <div className="h-16 w-16 bg-muted rounded-full flex items-center justify-center mx-auto">
                  <Key className="h-8 w-8 text-muted-foreground/50" />
                </div>
                <h3 className="font-semibold text-lg text-foreground">未选择 API Key</h3>
                <p className="text-muted-foreground text-sm max-w-xs mx-auto">
                  请从左侧列表选择一个 API Key 查看详情、管理权限或查看调用日志
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* 弹窗组件保持原逻辑 */}
      <Dialog open={visible} onOpenChange={setVisible}>
        <DialogContent className="max-w-[500px]">
          <DialogHeader>
            <DialogTitle>{isEditing ? '编辑 API Key' : '创建 API Key'}</DialogTitle>
            <DialogDescription>
              {isEditing ? '修改 API Key 的基本信息和权限设置' : '创建一个新的 API Key，用于访问系统 API'}
            </DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSave)} className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>名称 <span className="text-destructive">*</span></FormLabel>
                    <FormControl>
                      <Input {...field} required placeholder="例如：开发环境密钥" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="permissions"
                render={({ field }) => {
                  const selectedPermission = typeof field.value === 'string' ? field.value : ''
                  const handlePermissionChange = (value: string) => {
                    field.onChange(value || null)
                  }
                  return (
                    <FormItem>
                      <FormLabel>权限</FormLabel>
                      <Select value={selectedPermission} onValueChange={handlePermissionChange}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="请选择权限范围" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {PERMISSION_OPTIONS.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )
                }}
              />
              <FormField
                control={form.control}
                name="is_active"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3 bg-muted/20">
                    <div className="space-y-0.5">
                      <FormLabel className="text-sm font-semibold">启用状态</FormLabel>
                      <div className="text-xs text-muted-foreground">禁用后该 Key 将无法调用任何接口</div>
                    </div>
                    <FormControl>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                  </FormItem>
                )}
              />
              <DialogFooter className="gap-2 sm:gap-0">
                <Button type="button" variant="ghost" onClick={() => setVisible(false)}>
                  取消
                </Button>
                <Button type="submit">保存更改</Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <Dialog open={!!newApiKey} onOpenChange={() => {
        setNewApiKey(null)
        setNewApiKeyId(null)
        if (newApiKeyId && selectedApiKey?.id === newApiKeyId) {
          setSelectedApiKey(prev => prev ? { ...prev, key: newApiKey || undefined } : null)
        }
      }}>
        <DialogContent className="max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-green-600">
              <span className="h-2 w-2 rounded-full bg-green-600" />
              API Key 生成成功
            </DialogTitle>
            <DialogDescription>
              请立即复制并妥善保管此 Key。出于安全考虑，关闭此窗口后将无法再次查看完整密钥。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="p-4 bg-muted/50 rounded-lg border flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted-foreground">API KEY</span>
                <span className="text-xs text-muted-foreground">点击下方按钮复制</span>
              </div>
              <code className="text-sm font-mono break-all bg-background p-2 rounded border">
                {newApiKey}
              </code>
            </div>
            <Button
              className="w-full"
              size="lg"
              onClick={() => {
                if (newApiKey) handleCopy(newApiKey)
              }}
            >
              <Copy className="h-4 w-4 mr-2" />
              一键复制密钥
            </Button>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setNewApiKey(null)
              setNewApiKeyId(null)
              if (newApiKeyId && selectedApiKey?.id === newApiKeyId) {
                setSelectedApiKey(prev => prev ? { ...prev, key: newApiKey || undefined } : null)
              }
            }}>我已保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="text-destructive">确认删除此 API Key？</AlertDialogTitle>
            <AlertDialogDescription>
              此操作将永久删除该 API Key。任何使用此 Key 的应用将立即无法访问接口。此操作无法撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive hover:bg-destructive/90"
              onClick={() => {
                if (deleteTargetId) {
                  handleDelete(deleteTargetId)
                  setDeleteDialogOpen(false)
                  setDeleteTargetId(null)
                }
              }}
            >
              确认删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={regenerateDialogOpen} onOpenChange={setRegenerateDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认重新生成密钥？</AlertDialogTitle>
            <AlertDialogDescription>
              重新生成后，<strong className="text-destructive">旧的密钥将立即失效</strong>。您需要更新所有使用旧密钥的应用程序。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (regenerateTargetId) {
                  handleRegenerate(regenerateTargetId)
                }
              }}
            >
              确认重置
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export default ApiKeyManagement
