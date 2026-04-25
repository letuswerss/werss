import React, { useState, useEffect } from 'react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import {
  listConfigs,
  createConfig,
  updateConfig,
  deleteConfig
} from '@/api/configManagement'
import type { ConfigManagement } from '@/types/configManagement'
import { Plus, Edit, Trash2, Loader2, AlertCircle, Search } from 'lucide-react'
import { Textarea } from '@/components/ui/textarea'

const ConfigList: React.FC = () => {
  const [configList, setConfigList] = useState<ConfigManagement[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteTargetKey, setDeleteTargetKey] = useState<string | null>(null)
  const [modalTitle, setModalTitle] = useState('添加配置')
  const [formData, setFormData] = useState({
    config_key: '',
    config_value: '',
    description: ''
  })
  const [isEditMode, setIsEditMode] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const { toast } = useToast()

  const fetchConfigs = async () => {
    try {
      setLoading(true)
      const res = await listConfigs({
        page: pagination.current - 1,
        pageSize: pagination.pageSize
      }) as unknown as { list?: ConfigManagement[]; data?: { list?: ConfigManagement[]; total?: number }; total?: number }
      setConfigList(res.list || res.data?.list || [])
      setPagination(prev => ({ ...prev, total: res.total || res.data?.total || 0 }))
      setError('')
    } catch (err: any) {
      setError(err instanceof Error ? err.message : '获取配置列表失败')
      toast({
        variant: "destructive",
        title: "错误",
        description: err instanceof Error ? err.message : '获取配置列表失败'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConfigs()
  }, [pagination.current, pagination.pageSize])

  const showAddModal = () => {
    setModalTitle('添加配置')
    setIsEditMode(false)
    setFormData({ config_key: '', config_value: '', description: '' })
    setDialogOpen(true)
  }

  const editConfigItem = (record: ConfigManagement) => {
    setModalTitle('编辑配置')
    setIsEditMode(true)
    setFormData({
      config_key: record.config_key,
      config_value: record.config_value,
      description: record.description || ''
    })
    setDialogOpen(true)
  }

  const handleSubmit = async () => {
    if (!formData.config_key || !formData.config_value) {
      toast({
        variant: "destructive",
        title: "错误",
        description: "请填写配置键和配置值"
      })
      return
    }

    try {
      if (isEditMode) {
        await updateConfig(formData.config_key, {
          config_key: formData.config_key,
          config_value: formData.config_value,
          description: formData.description
        } as any)
      } else {
        await createConfig({
          config_key: formData.config_key,
          config_value: formData.config_value,
          description: formData.description
        } as any)
      }
      setDialogOpen(false)
      toast({
        title: "成功",
        description: isEditMode ? "配置已更新" : "配置已创建"
      })
      fetchConfigs()
    } catch (err: any) {
      toast({
        variant: "destructive",
        title: "错误",
        description: err instanceof Error ? err.message : '保存配置失败'
      })
    }
  }

  const deleteConfigItem = (key: string) => {
    setDeleteTargetKey(key)
    setDeleteDialogOpen(true)
  }

  const confirmDelete = async () => {
    if (!deleteTargetKey) return
    try {
      await deleteConfig(deleteTargetKey)
      setDeleteDialogOpen(false)
      setDeleteTargetKey(null)
      toast({
        title: "成功",
        description: "配置已删除"
      })
      fetchConfigs()
    } catch (err: any) {
      toast({
        variant: "destructive",
        title: "错误",
        description: err instanceof Error ? err.message : '删除配置失败'
      })
    }
  }

  const filteredConfigs = searchQuery.trim()
    ? configList.filter(c =>
        c.config_key.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.config_value.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (c.description || '').toLowerCase().includes(searchQuery.toLowerCase())
      )
    : configList

  const totalPages = Math.ceil(pagination.total / pagination.pageSize)

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 text-foreground">
          配置管理
        </h1>
        <p className="text-muted-foreground text-sm">
          管理系统配置项和参数设置
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle>配置列表</CardTitle>
            <CardDescription>管理系统配置项</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="搜索配置键、值或描述..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 w-[260px]"
              />
            </div>
            <Button
              onClick={showAddModal}
            >
              <Plus className="h-4 w-4 mr-2" />
              添加配置
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>配置键</TableHead>
                  <TableHead className="w-[30%]">配置值</TableHead>
                  <TableHead>描述</TableHead>
                  <TableHead className="w-[150px]">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={4} className="h-24 text-center">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                    </TableCell>
                  </TableRow>
                ) : filteredConfigs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                      {searchQuery ? '未找到匹配的配置项' : '暂无数据'}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredConfigs.map((config) => (
                    <TableRow key={config.config_key}>
                      <TableCell className="font-medium">{config.config_key}</TableCell>
                      <TableCell className="max-w-[300px] truncate" title={config.config_value}>
                        {config.config_value}
                      </TableCell>
                      <TableCell>{config.description || '-'}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => editConfigItem(config)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteConfigItem(config.config_key)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                共 {pagination.total} 条，第 {pagination.current} / {totalPages} 页
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPagination(prev => ({ ...prev, current: Math.max(1, prev.current - 1) }))}
                  disabled={pagination.current === 1}
                >
                  上一页
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPagination(prev => ({ ...prev, current: Math.min(totalPages, prev.current + 1) }))}
                  disabled={pagination.current === totalPages}
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 添加/编辑配置对话框 */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{modalTitle}</DialogTitle>
            <DialogDescription>配置系统参数</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="config_key">配置键 *</Label>
              <Input
                id="config_key"
                value={formData.config_key}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, config_key: e.target.value })}
                disabled={isEditMode}
                placeholder="请输入配置键"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="config_value">配置值 *</Label>
              <Input
                id="config_value"
                value={formData.config_value}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, config_value: e.target.value })}
                placeholder="请输入配置值"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">描述</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData({ ...formData, description: e.target.value })}
                placeholder="请输入描述"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>取消</Button>
            <Button onClick={handleSubmit}>
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>确定要删除此配置吗？</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>取消</Button>
            <Button variant="destructive" onClick={confirmDelete}>删除</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default ConfigList
