import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Upload } from '@/components/extensions/upload'
import { Message } from '@/utils/message'
import { getTag, createTag, updateTag } from '@/api/tagManagement'
import type { TagCreate } from '@/types/tagManagement'
import { uploadFile } from '@/api/file'
import MpMultiSelect from '@/components/MpMultiSelect'
import { Image, Edit, ArrowLeft } from 'lucide-react'

const TagForm: React.FC = () => {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = !!id
  const [loading, setLoading] = useState(false)
  const [formLoading, setFormLoading] = useState(false)
  const [showMpSelector, setShowMpSelector] = useState(false)
  const form = useForm<TagCreate & { mps_id: any[] }>({
    defaultValues: {
      name: '',
      cover: '',
      intro: '',
      status: 1,
      mps_id: []
    },
    mode: 'onChange'
  })

  useEffect(() => {
    if (id) {
      fetchTag(id)
    }
  }, [id])

  const fetchTag = async (tagId: string) => {
    try {
      setLoading(true)
      const res = await getTag(tagId)
      const data = (res as any).data || res
      form.reset({
        ...data,
        mps_id: JSON.parse(data.mps_id || '[]')
      })
    } catch (error) {
      Message.error(t('tags.messages.fetchDetailFailed'))
    } finally {
      setLoading(false)
    }
  }

  const handleUploadChange = async (fileList: any[]): Promise<void> => {
    const file = fileList[0]?.originFile || fileList[0]?.file

    if (!file?.type?.startsWith('image/')) {
      Message.error(t('tags.messages.invalidImageFile'))
      return
    }

    if (file.size > 2 * 1024 * 1024) {
      Message.error(t('tags.messages.imageSizeExceeded'))
      return
    }

    try {
      const res = await uploadFile(file)
      console.log(res)
      const data = (res as any).data || res
      form.setValue('cover', data.url)
    } catch (error: any) {
      console.error('上传错误:', error)
      Message.error(`${t('tags.messages.uploadFailed')}: ${error.response?.data?.message || error.message || t('common.errors.serverError')}`)
    }
    return
  }

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.target as HTMLImageElement
    img.src = '/default-cover.png'
  }

  const handleSubmit = async (values: TagCreate & { mps_id: any[] }) => {
    try {
      setFormLoading(true)
      const submitData = {
        ...values,
        mps_id: JSON.stringify(values.mps_id || [])
      }

      if (isEdit) {
        await updateTag(id!, submitData)
        Message.success(t('tags.messages.updateSuccess'))
      } else {
        await createTag(submitData)
        Message.success(t('tags.messages.createSuccess'))
      }
      navigate('/tags')
    } catch (error) {
      Message.error(isEdit ? t('tags.messages.updateFailed') : t('tags.messages.createFailed'))
    } finally {
      setFormLoading(false)
    }
  }

  const cover = form.watch('cover')
  const mpsId = form.watch('mps_id') || []

  return (
    <div className="p-5 max-w-[800px] mx-auto">
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          {t('common.back')}
        </Button>
        <h1 className="text-2xl font-semibold mb-1">
          {isEdit ? t('tags.editTitle') : t('tags.addTitle')}
        </h1>
        <p className="text-sm text-muted-foreground">{t('tags.tagInfo')}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{isEdit ? t('tags.editTitle') : t('tags.addTitle')}</CardTitle>
          <CardDescription>{t('tags.formDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-muted-foreground">{t('common.loading')}</div>
            </div>
          ) : (
            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t('tags.name')}</FormLabel>
                      <FormControl>
                        <Input placeholder={t('tags.namePlaceholder')} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="cover"
                  render={() => (
                    <FormItem>
                      <FormLabel>{t('tags.cover')}</FormLabel>
                      <FormControl>
                        <Upload
                          customRequest={handleUploadChange}
                          showUploadList={false}
                          accept="image/*"
                          limit={1}
                        >
                          <div className="relative w-[120px] h-[120px] cursor-pointer border border-dashed rounded group overflow-hidden">
                            {cover ? (
                              <img
                                src={cover}
                                alt="cover"
                                onError={handleImageError}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <Image className="h-8 w-8 text-muted-foreground" />
                              </div>
                            )}
                            <div className="absolute top-0 left-0 w-full h-full bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                              <Edit className="h-6 w-6 text-white" />
                            </div>
                          </div>
                        </Upload>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="intro"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t('tags.intro')}</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder={t('tags.introPlaceholder')}
                          rows={3}
                          {...field}
                          value={field.value || ''}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="status"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t('tags.status')}</FormLabel>
                      <Select
                        value={field.value?.toString()}
                        onValueChange={(value) => field.onChange(parseInt(value))}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder={t('tags.statusPlaceholder')} />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="1">{t('tags.statusEnabled')}</SelectItem>
                          <SelectItem value="0">{t('tags.statusDisabled')}</SelectItem>
                          <SelectItem value="2">{t('tags.statusBlocked')}</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="mps_id"
                  render={() => (
                    <FormItem>
                      <FormLabel>{t('tags.mps')}</FormLabel>
                      <div className="flex gap-2">
                        <Input
                          value={mpsId.map((mp: any) => mp.id?.toString() || '').join(',')}
                          placeholder={t('tags.mpsPlaceholder')}
                          readOnly
                          className="flex-1 max-w-[300px]"
                        />
                        <Button
                          type="button"
                          onClick={() => setShowMpSelector(true)}
                        >
                          {t('tags.select')}
                        </Button>
                      </div>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="flex gap-2">
                  <Button type="submit" disabled={formLoading}>
                    {formLoading ? t('tags.submitting') : t('tags.submit')}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                    {t('common.cancel')}
                  </Button>
                </div>
              </form>
            </Form>
          )}
        </CardContent>
      </Card>

      <Dialog open={showMpSelector} onOpenChange={setShowMpSelector}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>{t('tags.selectMps')}</DialogTitle>
            <DialogDescription>{t('tags.selectMpsDescription')}</DialogDescription>
          </DialogHeader>
          <MpMultiSelect
            value={mpsId}
            onChange={(value) => form.setValue('mps_id', value)}
          />
          <div className="flex justify-end mt-4">
            <Button onClick={() => setShowMpSelector(false)}>
              {t('common.confirm')}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default TagForm
