import { useState, useImperativeHandle, forwardRef } from 'react'
import { useForm } from 'react-hook-form'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Message } from '@/utils/message'
import { exportArticles } from '@/api/tools'

interface ExportModalProps {
  onConfirm?: (formData: any) => void
}

export interface ExportModalRef {
  show: (mp_id: string, ids: any[], mp_name?: string) => void
  hide: () => void
}

interface FormValues {
  scope: string
  format: string
  page_count: number
  mp_id: string
  ids: any[]
  add_title: boolean
  remove_images: boolean
  remove_links: boolean
  zip_filename: string
}

const ExportModal = forwardRef<ExportModalRef, ExportModalProps>(({ onConfirm }, ref) => {
  const [open, setOpen] = useState(false)
  
  const form = useForm<FormValues>({
    defaultValues: {
      scope: 'all',
      format: 'md', // 默认选择 markdown
      page_count: 0, // 0 表示导出所有，不再显示在界面上
      mp_id: '',
      ids: [],
      add_title: true,
      remove_images: false,
      remove_links: false,
      zip_filename: '',
    }
  })

  const show = (mp_id: string, ids: any[], mp_name?: string) => {
    // 调试日志：检查接收到的参数
    console.log('ExportModal.show 接收参数:', {
      mp_id,
      ids,
      idsType: typeof ids,
      idsIsArray: Array.isArray(ids),
      idsLength: ids?.length,
      mp_name
    })
    
    const newFormData = {
      scope: ids && ids.length > 0 ? 'selected' : 'all',
      format: 'md', // 默认选择 markdown
      page_count: 0, // 0 表示导出所有
      mp_id,
      ids: ids || [], // 确保 ids 是数组
      add_title: true,
      remove_images: false,
      remove_links: false,
      zip_filename: mp_name && mp_name !== '全部' ? `${mp_name}_文章.zip` : '全部文章.zip'
    }
    
    console.log('ExportModal.show 设置表单数据:', {
      ...newFormData,
      ids: newFormData.ids,
      idsLength: newFormData.ids.length
    })
    
    form.reset(newFormData)
    setOpen(true)
  }

  const hide = () => {
    setOpen(false)
  }

  useImperativeHandle(ref, () => ({
    show,
    hide
  }))

  const handleExport = async (exportScope: 'all' | 'selected') => {
    try {
      const values = form.getValues()
      // 验证选择了导出格式
      if (!values.format) {
        Message.error('请选择一个导出格式')
        return
      }
      
      // 如果是导出选中，但没有选中文章，提示错误
      if (exportScope === 'selected' && (!values.ids || values.ids.length === 0)) {
        Message.error('请先选择要导出的文章')
        return
      }
      
      // 根据导出范围设置参数，将单个格式转换为数组格式（API 期望数组）
      const exportParams = {
        ...values,
        scope: exportScope,
        format: [values.format], // 转换为数组格式
        // API 会根据 scope 和 ids 来设置 doc_id
      }
      
      // 调试日志：检查传递的参数
      console.log('导出参数:', {
        scope: exportScope,
        ids: values.ids,
        idsLength: values.ids?.length,
        mp_id: values.mp_id,
        format: exportParams.format
      })
      
      await submitExport(exportParams)
      onConfirm?.(exportParams)
      hide()
    } catch (error: any) {
      // 错误已在 submitExport 中处理
      console.error('导出处理失败:', error)
    }
  }

  const submitExport = async (params: any) => {
    try {
      const result: any = await exportArticles(params)
      // http 拦截器在 code === 0 时返回 response.data.data 或 response.data
      // 如果能执行到这里，说明请求成功了（拦截器已经处理了错误情况）
      // 检查 result 的结构
      let message = '导出任务已启动，请稍后下载文件'
      let exportPath = null
      
      if (result && typeof result === 'object') {
        // 如果 result 有 code 字段，说明拦截器返回了完整的 response.data
        if ('code' in result) {
          message = result.message || result.data?.message || message
          exportPath = result.data?.export_path
        } else {
          // 如果 result 没有 code 字段，说明拦截器返回了 response.data.data
          // 这种情况下，result 就是 data 字段的内容
          message = result.message || message
          exportPath = result.export_path
        }
      }
      
      Message.success(message)
      
      // 如果有导出路径，记录日志
      if (exportPath) {
        console.log('导出文件路径:', exportPath)
      }
    } catch (error: any) {
      console.error('导出失败:', error)
      // 如果错误已经被拦截器处理过（显示过错误消息），就不再重复显示
      // 检查是否是字符串错误（拦截器返回的）
      if (typeof error === 'string') {
        // 拦截器已经显示过错误消息了，这里不需要再显示
        return
      }
      // 只有在拦截器没有显示错误消息的情况下才显示
      const errorMsg = error?.response?.data?.message || error?.message || '导出失败，请稍后重试'
      Message.error(errorMsg)
    }
  }

  // 实时监听 ids 的变化
  const idsValue = form.watch('ids')

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>导出设置</DialogTitle>
          <DialogDescription>配置导出选项</DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <div className="space-y-4">
            <FormField
              control={form.control}
              name="format"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>导出格式</FormLabel>
                  <FormControl>
                    <RadioGroup
                      value={field.value}
                      onValueChange={field.onChange}
                      className="space-y-2"
                    >
                      {[
                        { value: 'md', label: 'MarkDown' },
                        { value: 'pdf', label: 'PDF归档' },
                        { value: 'docx', label: 'WORD文档' },
                        { value: 'json', label: 'JSON附加信息' },
                        { value: 'csv', label: 'Excel列表' }
                      ].map((fmt) => (
                        <div key={fmt.value} className="flex items-center space-x-2">
                          <RadioGroupItem value={fmt.value} id={fmt.value} />
                          <Label
                            htmlFor={fmt.value}
                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                          >
                            {fmt.label}
                          </Label>
                      </div>
                    ))}
                    </RadioGroup>
                  </FormControl>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="zip_filename"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>文件名</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="请输入导出文件名（可选）"
                      {...field}
                    />
                  </FormControl>
                </FormItem>
              )}
            />
            <div className="space-y-2">
              <div className="text-sm font-medium">导出选项</div>
              <FormField
                control={form.control}
                name="add_title"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                        添加标题
                      </label>
                    </div>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="remove_images"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                        移除图片
                      </label>
                    </div>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="remove_links"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                        移除链接
                      </label>
                    </div>
                  </FormItem>
                )}
              />
            </div>
          </div>
        </Form>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={hide}>取消</Button>
          <Button 
            variant="outline" 
            onClick={() => handleExport('all')}
          >
            导出所有
          </Button>
          <Button 
            onClick={() => handleExport('selected')}
            disabled={!idsValue || idsValue.length === 0}
          >
            导出选中
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
})

ExportModal.displayName = 'ExportModal'

export default ExportModal
