import React, { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { useToast } from '@/hooks/use-toast'
import { getSettings, saveSettings, type AppSettings } from '@/utils/settings'
import { useTheme } from '@/components/theme-provider'
import { getConfig, createConfig, updateConfig } from '@/api/configManagement'
import dayjs from 'dayjs'
import { Input } from '@/components/ui/input'
import { CalendarIcon, Loader2, Trash2 } from 'lucide-react'
import { format } from 'date-fns'
import { cn } from '@/lib/utils'

const DEFAULT_TAG_EXTRACT_PROMPT = `请从以下文章中提取 {{max_tags}} 个最核心的**具体**标签关键词。

【提取优先级（按重要性排序）】：
1. **公司名称**：文章中提到的所有公司、企业、组织名称（如：字节跳动、腾讯、阿里巴巴、OpenAI、Anthropic、英伟达、华为、小米等）
2. **产品/服务名称**：具体的产品、服务、平台名称（如：ChatGPT、Claude、豆包、微信、抖音、iOS、Android等）
3. **技术/工具名称**：具体的技术、框架、工具、协议名称（如：React、TensorFlow、Kubernetes、HTTP/3等）
4. **人物名称**：科技界、商业界的重要人物（如：马斯克、李彦宏、张一鸣等）
5. **特定事件/项目**：具体的项目、事件、活动名称（如：诺贝尔奖、登月计划等）
6. **特定领域/概念**：具体的细分领域或专业概念（如：自动驾驶、量子计算、区块链等）

【重要要求】：
1. **必须提取公司名称**：如果文章提到公司，公司名称必须包含在标签中
2. 标签词必须**具体且有区分度**，避免通用词汇
3. 避免提取：AI、大语言模型、云计算、机器学习、技术、产品等过于宽泛的词
4. 每个标签词 2-15 个字（公司名称可以更长）
5. 按重要性排序（公司名称通常最重要）
6. 只返回 JSON 数组格式，不要包含任何解释或思考过程

【好的示例】：
- 好："字节跳动"、"豆包视频"、"Seedance 1.5"、"火山引擎"、"Anthropic"、"Claude"、"诺贝尔奖"、"Crossplane"、"快手OneRec"、"李彦宏"、"DeepSeek"、"英伟达"、"NVIDIA"
- 差："AI"、"大语言模型"、"云计算"、"人工智能"、"技术"、"产品"、"公司"
{{custom_tags_hint}}

文章：
{{text}}

返回格式：["具体标签1", "具体标签2", "具体标签3"]`

const MEDICAL_TAG_EXTRACT_PROMPT = `请从以下医学文章中提取 {{max_tags}} 个最核心、最适合检索和聚类的标签关键词。

【提取优先级（按重要性排序）】：
1. **疾病 / 诊断名称**：如弥漫大B细胞淋巴瘤、肾移植排斥反应、肺腺癌、糖尿病肾病
2. **药物 / 治疗方案**：如地塞米松、利妥昔单抗、CAR-T、PD-1 抑制剂、化疗、放疗
3. **手术 / 操作 / 检查**：如肾移植、骨髓穿刺、PET-CT、病理活检、免疫组化
4. **科室 / 专业方向**：如肿瘤科、血液科、肾内科、移植科、影像科
5. **指南 / 分型 / 指标 / 并发症**：如 NCCN 指南、Ann Arbor 分期、CD20、感染、复发
6. **机构 / 企业 / 产品名**：仅在文章中确实重要时提取

【重要要求】：
1. 优先提取医学上有明确指向性的术语，避免空泛词
2. 可以提取疾病名、药物通用名、治疗方案、检查名、并发症、分期分型
3. 避免提取：医学、治疗、疾病、患者、研究、专家、医院等过于宽泛的词
4. 标签尽量具体，便于后续聚类、检索和统计
5. 只返回 JSON 数组格式，不要包含任何解释或思考过程

【好的示例】：
- 好："弥漫大B细胞淋巴瘤"、"肾移植"、"地塞米松"、"利妥昔单抗"、"CAR-T"、"肿瘤科"
- 差："医学"、"治疗"、"患者"、"专家"、"医院"
{{custom_tags_hint}}

文章：
{{text}}

返回格式：["标签1", "标签2", "标签3"]`

const LEGAL_TAG_EXTRACT_PROMPT = `请从以下法律文章中提取 {{max_tags}} 个最核心、最适合检索和聚类的标签关键词。

【提取优先级（按重要性排序）】：
1. **法律 / 法规 / 司法解释名称**：如公司法、民法典、刑法、反垄断法、最高法司法解释
2. **案由 / 法律问题 / 制度概念**：如劳动争议、合同解除、侵权责任、股东出资、行政处罚
3. **程序环节 / 裁判结果**：如再审、二审、执行异议、不予起诉、驳回诉讼请求
4. **主体类型 / 机构名称**：如最高人民法院、检察院、证监会、用人单位、平台企业
5. **具体罪名 / 请求权 / 责任类型**：如诈骗罪、违约责任、缔约过失责任、不当得利
6. **重要案例 / 文件 / 指引名称**：如指导性案例、典型案例、合规指引

【重要要求】：
1. 优先提取具有明确法律意义的术语、制度、法条名称、案由和机构名
2. 可以提取具体法律问题、程序节点、裁判观点关键词
3. 避免提取：法律、案件、法院、规定、问题、企业、当事人等过于宽泛的词
4. 标签应尽量具体，便于归类、检索和专题分析
5. 只返回 JSON 数组格式，不要包含任何解释或思考过程

【好的示例】：
- 好："民法典"、"劳动争议"、"竞业限制"、"行政处罚"、"诈骗罪"、"最高人民法院"
- 差："法律"、"案件"、"法院"、"规定"、"问题"
{{custom_tags_hint}}

文章：
{{text}}

返回格式：["标签1", "标签2", "标签3"]`

const CUSTOM_TAG_EXTRACT_PROMPT = `请从以下文章中提取 {{max_tags}} 个最核心、最适合后续检索、聚类和统计的标签关键词。

【你的提取规则】：
1. 优先提取最具体、最有区分度的实体、主题、术语、机构、产品、药物、法规、疾病、技术或事件名称
2. 可以根据文章领域自行判断哪些标签最有价值
3. 避免提取过于空泛的词，如“技术”“行业”“文章”“问题”“研究”等
4. 标签应尽量具体，便于后续归类、搜索和专题分析
5. 只返回 JSON 数组格式，不要包含任何解释或思考过程

{{custom_tags_hint}}

文章：
{{text}}

返回格式：["标签1", "标签2", "标签3"]`

const TAG_PROMPT_PRESETS = [
  { key: 'tech', label: '科技', prompt: DEFAULT_TAG_EXTRACT_PROMPT },
  { key: 'medical', label: '医学', prompt: MEDICAL_TAG_EXTRACT_PROMPT },
  { key: 'legal', label: '法律', prompt: LEGAL_TAG_EXTRACT_PROMPT },
] as const

type TagPromptPresetKey = typeof TAG_PROMPT_PRESETS[number]['key'] | 'custom'

const detectTagPromptPreset = (prompt: string): TagPromptPresetKey => {
  const trimmed = prompt.trim()
  const matched = TAG_PROMPT_PRESETS.find((item) => item.prompt.trim() === trimmed)
  return matched ? matched.key : 'custom'
}

const Settings: React.FC = () => {
  const tagPromptTextareaRef = useRef<HTMLTextAreaElement | null>(null)
  const [settings, setSettings] = useState<AppSettings>(getSettings())
  const [collectStartDate, setCollectStartDate] = useState<Date | null>(null)
  const [tempCollectStartDate, setTempCollectStartDate] = useState<Date | null>(null)
  const [loading, setLoading] = useState(false)
  const [tagPrompt, setTagPrompt] = useState(DEFAULT_TAG_EXTRACT_PROMPT)
  const [tempTagPrompt, setTempTagPrompt] = useState(DEFAULT_TAG_EXTRACT_PROMPT)
  const [tagPromptPreset, setTagPromptPreset] = useState<TagPromptPresetKey>('tech')
  const [tagPromptLoading, setTagPromptLoading] = useState(false)
  const [storeArticleImages, setStoreArticleImages] = useState(true)
  const [storeArticleImagesLoading, setStoreArticleImagesLoading] = useState(false)
  const [retentionEnabled, setRetentionEnabled] = useState(false)
  const [retentionEnabledSaving, setRetentionEnabledSaving] = useState(false)
  const [retentionDays, setRetentionDays] = useState(7)
  const [tempRetentionDays, setTempRetentionDays] = useState(7)
  const [retentionBasis, setRetentionBasis] = useState<'created_at' | 'publish_time'>('created_at')
  const [tempRetentionBasis, setTempRetentionBasis] = useState<'created_at' | 'publish_time'>('created_at')
  const [retentionDetailLoading, setRetentionDetailLoading] = useState(false)
  const [retentionDetailSaving, setRetentionDetailSaving] = useState(false)
  const { toast } = useToast()
  const { theme, setTheme } = useTheme()

  useEffect(() => {
    // 监听设置变更事件
    const handleSettingsChange = (e: CustomEvent<AppSettings>) => {
      setSettings(e.detail)
    }

    window.addEventListener('settingsChanged', handleSettingsChange as EventListener)

    // 加载采集起始时间配置
    loadCollectStartDate()
    loadTagExtractPrompt()
    loadStoreArticleImages()
    loadArticleRetention()

    return () => {
      window.removeEventListener('settingsChanged', handleSettingsChange as EventListener)
    }
  }, [])

  const loadStoreArticleImages = async () => {
    try {
      const res = await getConfig('minio.store_article_images')
      const data = (res as any)?.data || res
      if (data?.config_value !== undefined && data?.config_value !== null && String(data.config_value).trim() !== '') {
        const v = String(data.config_value).toLowerCase()
        setStoreArticleImages(v === 'true' || v === '1')
      } else {
        setStoreArticleImages(true)
      }
    } catch (error: any) {
      if (error?.response?.status === 404 || error?.message?.includes('404')) {
        setStoreArticleImages(true)
      } else {
        console.error('加载图片转存配置失败:', error)
        setStoreArticleImages(true)
      }
    }
  }

  const handleStoreArticleImagesChange = async (checked: boolean) => {
    setStoreArticleImagesLoading(true)
    try {
      try {
        await updateConfig('minio.store_article_images', {
          config_key: 'minio.store_article_images',
          config_value: checked ? 'true' : 'false',
          description: 'MinIO 可用时是否将公众号文章相关图片转存到对象存储',
        } as any)
      } catch (error: any) {
        if (error?.response?.status === 404 || error?.response?.statusCode === 404 || error?.message?.includes('404') || error?.message?.includes('Config not found')) {
          await createConfig({
            config_key: 'minio.store_article_images',
            config_value: checked ? 'true' : 'false',
            description: 'MinIO 可用时是否将公众号文章相关图片转存到对象存储',
          })
        } else {
          throw error
        }
      }
      setStoreArticleImages(checked)
      toast({
        title: '已保存',
        description: checked ? '已开启图片转存（需 MinIO 可用时生效）' : '已关闭转存，将尽量使用微信侧图片链接',
      })
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: '保存失败',
        description: error?.message || '请稍后重试',
      })
    } finally {
      setStoreArticleImagesLoading(false)
    }
  }

  const parseConfigBool = (v: unknown, defaultVal: boolean) => {
    if (v === undefined || v === null || String(v).trim() === '') return defaultVal
    const s = String(v).toLowerCase()
    return s === 'true' || s === '1'
  }

  const parseRetentionDays = (v: unknown) => {
    const n = parseInt(String(v ?? ''), 10)
    if (Number.isNaN(n) || n < 1) return 7
    return Math.min(9999, n)
  }

  const loadArticleRetention = async () => {
    setRetentionDetailLoading(true)
    try {
      const loadKey = async (key: string) => {
        try {
          const res = await getConfig(key)
          const data = (res as any)?.data || res
          return data?.config_value
        } catch (e: any) {
          if (e?.response?.status === 404 || e?.message?.includes?.('404')) {
            return undefined
          }
          throw e
        }
      }
      const en = await loadKey('article.retention.enabled')
      const days = await loadKey('article.retention.days')
      const basis = await loadKey('article.retention.basis')
      setRetentionEnabled(parseConfigBool(en, false))
      const d = parseRetentionDays(days)
      setRetentionDays(d)
      setTempRetentionDays(d)
      const b =
        String(basis || 'created_at').toLowerCase() === 'publish_time' ? 'publish_time' : 'created_at'
      setRetentionBasis(b)
      setTempRetentionBasis(b)
    } catch (error) {
      console.error('加载文章定期清理配置失败:', error)
      setRetentionEnabled(false)
      setRetentionDays(7)
      setTempRetentionDays(7)
      setRetentionBasis('created_at')
      setTempRetentionBasis('created_at')
    } finally {
      setRetentionDetailLoading(false)
    }
  }

  const handleRetentionEnabledChange = async (checked: boolean) => {
    setRetentionEnabledSaving(true)
    try {
      const payload = {
        config_key: 'article.retention.enabled',
        config_value: checked ? 'true' : 'false',
        description: '是否启用按保留天数定期清理旧文章',
      } as any
      try {
        await updateConfig('article.retention.enabled', payload)
      } catch (error: any) {
        if (error?.response?.status === 404 || error?.response?.statusCode === 404 || error?.message?.includes('404') || error?.message?.includes('Config not found')) {
          await createConfig({
            config_key: 'article.retention.enabled',
            config_value: checked ? 'true' : 'false',
            description: '是否启用按保留天数定期清理旧文章',
          })
        } else {
          throw error
        }
      }
      setRetentionEnabled(checked)
      toast({
        title: '已保存',
        description: checked
          ? '已启用定期清理（需服务以定时任务方式运行且 server.enable_job 为真时执行）'
          : '已关闭定期自动清理',
      })
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: '保存失败',
        description: error?.message || '请稍后重试',
      })
    } finally {
      setRetentionEnabledSaving(false)
    }
  }

  const handleSaveArticleRetention = async () => {
    if (tempRetentionDays < 1) {
      toast({ variant: 'destructive', title: '错误', description: '保留天数至少为 1' })
      return
    }
    setRetentionDetailSaving(true)
    try {
      const dayStr = String(Math.min(9999, Math.max(1, Math.floor(tempRetentionDays))))
      const basisStr = tempRetentionBasis
      const dayPayload = {
        config_key: 'article.retention.days',
        config_value: dayStr,
        description: '文章保留最近多少天（按时间基准与当前时间比较）',
      } as any
      const basisPayload = {
        config_key: 'article.retention.basis',
        config_value: basisStr,
        description: '清理时间基准：created_at=入库时间，publish_time=微信发布时间',
      } as any
      try {
        await updateConfig('article.retention.days', dayPayload)
      } catch (e: any) {
        if (e?.response?.status === 404 || e?.message?.includes?.('404') || e?.message?.includes?.('Config not found')) {
          await createConfig({ ...dayPayload })
        } else {
          throw e
        }
      }
      try {
        await updateConfig('article.retention.basis', basisPayload)
      } catch (e: any) {
        if (e?.response?.status === 404 || e?.message?.includes?.('404') || e?.message?.includes?.('Config not found')) {
          await createConfig({ ...basisPayload })
        } else {
          throw e
        }
      }
      setRetentionDays(parseRetentionDays(dayStr))
      setTempRetentionDays(parseRetentionDays(dayStr))
      setRetentionBasis(basisStr)
      setTempRetentionBasis(basisStr)
      toast({ variant: 'success', title: '成功', description: '文章保留策略已保存' })
    } catch (error: any) {
      const errMsg = error?.response?.data?.detail || error?.response?.data?.message || error?.message
      toast({
        variant: 'destructive',
        title: '保存失败',
        description: typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg),
      })
    } finally {
      setRetentionDetailSaving(false)
    }
  }

  const loadTagExtractPrompt = async () => {
    try {
      const res = await getConfig('article_tag.ai_prompt')
      const data = (res as any)?.data || res
      const value = data?.config_value ? String(data.config_value) : DEFAULT_TAG_EXTRACT_PROMPT
      setTagPrompt(value)
      setTempTagPrompt(value)
      setTagPromptPreset(detectTagPromptPreset(value))
    } catch (error: any) {
      if (error?.response?.status === 404 || error?.message?.includes('404')) {
        setTagPrompt(DEFAULT_TAG_EXTRACT_PROMPT)
        setTempTagPrompt(DEFAULT_TAG_EXTRACT_PROMPT)
        setTagPromptPreset('tech')
      } else {
        console.error('加载标签提取提示词失败:', error)
        setTagPrompt(DEFAULT_TAG_EXTRACT_PROMPT)
        setTempTagPrompt(DEFAULT_TAG_EXTRACT_PROMPT)
        setTagPromptPreset('tech')
      }
    }
  }

  // 加载采集起始时间配置
  const loadCollectStartDate = async () => {
    try {
      const res = await getConfig('collect_start_date')
      const data = (res as any)?.data || res
      if (data && data.config_value) {
        const date = dayjs(data.config_value).toDate()
        setCollectStartDate(date)
        setTempCollectStartDate(date)
      } else {
        // 默认值：2025-12-01
        const defaultDate = dayjs('2025-12-01').toDate()
        setCollectStartDate(defaultDate)
        setTempCollectStartDate(defaultDate)
      }
    } catch (error: any) {
      // 如果配置不存在（404），自动创建默认配置
      if (error?.response?.status === 404 || error?.message?.includes('404')) {
        const defaultDate = dayjs('2025-12-01').toDate()
        try {
          // 自动创建默认配置，避免后续的 404 错误
          await createConfig({
            config_key: 'collect_start_date',
            config_value: dayjs(defaultDate).format('YYYY-MM-DD'),
            description: '采集数据的起始时间，格式：YYYY-MM-DD'
          })
          setCollectStartDate(defaultDate)
          setTempCollectStartDate(defaultDate)
        } catch (createError: any) {
          // 如果创建失败，仍然使用默认值
          console.warn('自动创建采集起始时间配置失败:', createError)
          setCollectStartDate(defaultDate)
          setTempCollectStartDate(defaultDate)
        }
      } else {
        console.error('加载采集起始时间配置失败:', error)
        const defaultDate = dayjs('2025-12-01').toDate()
        setCollectStartDate(defaultDate)
        setTempCollectStartDate(defaultDate)
      }
    }
  }

  // 保存采集起始时间配置
  const handleSaveCollectStartDate = async () => {
    if (!tempCollectStartDate) {
      toast({
        variant: "destructive",
        title: "警告",
        description: "请选择采集起始时间"
      })
      return
    }

    setLoading(true)
    try {
      const dateStr = dayjs(tempCollectStartDate).format('YYYY-MM-DD')
      try {
        // 尝试更新现有配置
        await updateConfig('collect_start_date', {
          config_key: 'collect_start_date',
          config_value: dateStr,
          description: '采集数据的起始时间，格式：YYYY-MM-DD'
        } as any)
      } catch (error: any) {
        // 如果配置不存在（404），创建新配置
        if (error?.response?.status === 404 || error?.response?.statusCode === 404 || error?.message?.includes('404') || error?.message?.includes('Config not found')) {
          await createConfig({
            config_key: 'collect_start_date',
            config_value: dateStr,
            description: '采集数据的起始时间，格式：YYYY-MM-DD'
          } as any)
        } else {
          throw error
        }
      }
      setCollectStartDate(tempCollectStartDate)
      toast({
        variant: "success",
        title: "成功",
        description: "采集起始时间已保存"
      })
    } catch (error: any) {
      console.error('保存采集起始时间失败:', error)
      const errorMessage = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '保存采集起始时间失败'
      toast({
        variant: "destructive",
        title: "错误",
        description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage)
      })
    } finally {
      setLoading(false)
    }
  }

  const handleWatermarkChange = (enabled: boolean) => {
    const newSettings = { ...settings, watermarkEnabled: enabled }
    setSettings(newSettings)
    saveSettings(newSettings)
    toast({
      variant: "success",
      title: "成功",
      description: enabled ? '已启用水印' : '已关闭水印'
    })
  }

  const handleDarkModeChange = (enabled: boolean) => {
    const newSettings = { ...settings, darkMode: enabled }
    setSettings(newSettings)
    saveSettings(newSettings)
    // 使用新的 theme provider
    setTheme(enabled ? 'dark' : 'light')
    toast({
      variant: "success",
      title: "成功",
      description: enabled ? '已切换到暗色模式' : '已切换到亮色模式'
    })
  }

  const handleSaveTagPrompt = async () => {
    const value = tempTagPrompt.trim()
    if (!value) {
      toast({
        variant: "destructive",
        title: "错误",
        description: "标签提取提示词不能为空"
      })
      return
    }

    setTagPromptLoading(true)
    try {
      try {
        await updateConfig('article_tag.ai_prompt', {
          config_key: 'article_tag.ai_prompt',
          config_value: value,
          description: 'AI 标签提取提示词模板，支持 {{max_tags}}、{{custom_tags_hint}}、{{text}} 占位符'
        } as any)
      } catch (error: any) {
        if (error?.response?.status === 404 || error?.response?.statusCode === 404 || error?.message?.includes('404') || error?.message?.includes('Config not found')) {
          await createConfig({
            config_key: 'article_tag.ai_prompt',
            config_value: value,
            description: 'AI 标签提取提示词模板，支持 {{max_tags}}、{{custom_tags_hint}}、{{text}} 占位符'
          } as any)
        } else {
          throw error
        }
      }
      setTagPrompt(value)
      setTempTagPrompt(value)
      setTagPromptPreset(detectTagPromptPreset(value))
      toast({
        variant: "success",
        title: "成功",
        description: "标签提取提示词已保存"
      })
    } catch (error: any) {
      console.error('保存标签提取提示词失败:', error)
      const errorMessage = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '保存标签提取提示词失败'
      toast({
        variant: "destructive",
        title: "错误",
        description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage)
      })
    } finally {
      setTagPromptLoading(false)
    }
  }

  const isDateChanged = tempCollectStartDate && collectStartDate
    ? !dayjs(tempCollectStartDate).isSame(dayjs(collectStartDate), 'day')
    : false
  const isRetentionDetailChanged =
    tempRetentionDays !== retentionDays || tempRetentionBasis !== retentionBasis
  const isTagPromptChanged = tempTagPrompt.trim() !== tagPrompt.trim()

  const handleTagPromptPresetChange = (presetKey: string) => {
    if (presetKey === 'custom') {
      setTagPromptPreset('custom')
      const currentPreset = detectTagPromptPreset(tempTagPrompt)
      if (currentPreset !== 'custom') {
        setTempTagPrompt(CUSTOM_TAG_EXTRACT_PROMPT)
      }
      setTimeout(() => {
        tagPromptTextareaRef.current?.focus()
      }, 0)
      return
    }
    const preset = TAG_PROMPT_PRESETS.find((item) => item.key === presetKey)
    if (!preset) return
    setTagPromptPreset(preset.key)
    setTempTagPrompt(preset.prompt)
  }

  return (
    <div className="p-6 max-w-3xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 text-foreground">
          应用设置
        </h1>
        <p className="text-muted-foreground text-sm">
          自定义您的应用体验
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>设置</CardTitle>
          <CardDescription>管理您的应用偏好设置</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 水印设置 */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="watermark" className="text-base">显示水印</Label>
              <p className="text-sm text-muted-foreground">
                在页面上显示版权水印信息
              </p>
            </div>
            <Switch
              id="watermark"
              checked={settings.watermarkEnabled}
              onCheckedChange={handleWatermarkChange}
            />
          </div>

          <Separator />

          {/* 暗色模式设置 */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="darkmode" className="text-base">暗色模式</Label>
              <p className="text-sm text-muted-foreground">
                使用暗色主题，减少眼部疲劳
              </p>
            </div>
            <Switch
              id="darkmode"
              checked={theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)}
              onCheckedChange={handleDarkModeChange}
            />
          </div>

          <Separator />

          {/* 采集数据起始时间设置 */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="space-y-0.5">
              <Label className="text-base">采集数据起始时间</Label>
              <p className="text-sm text-muted-foreground">
                设置公众号文章采集的起始日期，系统将从该日期开始抓取文章
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-[240px] justify-start text-left font-normal",
                      !tempCollectStartDate && "text-muted-foreground"
                    )}
                    disabled={loading}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {tempCollectStartDate ? (
                      format(tempCollectStartDate, "yyyy-MM-dd")
                    ) : (
                      <span>选择日期</span>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="end">
                  <Calendar
                    mode="single"
                    selected={tempCollectStartDate || undefined}
                    onSelect={(date) => setTempCollectStartDate(date || null)}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
              <Button
                onClick={handleSaveCollectStartDate}
                disabled={loading || !tempCollectStartDate || !isDateChanged}
              >
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                保存
              </Button>
            </div>
          </div>

        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1 space-y-1.5">
              <CardTitle className="flex items-center gap-2">
                <Trash2 className="h-5 w-5 shrink-0" />
                文章定期清理
              </CardTitle>
              <CardDescription>
                按保留天数删除较早的文章（及关联的标签、AI 筛选记录）。默认保留最近 7 天；与{' '}
                <code className="text-[0.7rem]">config.yaml</code> 中{' '}
                <code className="text-[0.7rem]">article.retention</code> 一致。
              </CardDescription>
            </div>
            <Switch
              id="article-retention-enabled"
              className="mt-1 shrink-0"
              checked={retentionEnabled}
              disabled={retentionDetailLoading || retentionEnabledSaving}
              onCheckedChange={(v) => void handleRetentionEnabledChange(v)}
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="article-retention-enabled" className="text-base">
              启用定期清理
            </Label>
            <p className="text-sm text-muted-foreground max-w-xl">
              关闭时不会自动删除历史文章。开启后，在进程以{' '}
              <code className="text-[0.7rem]">-job True</code> 启动且{' '}
              <code className="text-[0.7rem]">server.enable_job</code> 为真时，按{' '}
              <code className="text-[0.7rem]">article.retention.cron</code>（默认每天 4:00）执行清理。
            </p>
          </div>

          <Separator />

          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="space-y-2 flex-1 min-w-0">
              <Label className="text-base">保留最近</Label>
              <p className="text-sm text-muted-foreground">
                早于「当前时间减去该天数」的文章会被清理（与下方时间基准配合）
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <Input
                  id="retention-days"
                  type="number"
                  min={1}
                  max={9999}
                  className="w-[120px]"
                  value={tempRetentionDays}
                  disabled={retentionDetailLoading}
                  onChange={(e) => {
                    const raw = e.target.value
                    if (raw === '') {
                      setTempRetentionDays(0)
                      return
                    }
                    const n = parseInt(raw, 10)
                    if (!Number.isNaN(n)) setTempRetentionDays(n)
                  }}
                />
                <span className="text-sm text-muted-foreground">天内的文章</span>
              </div>
            </div>
            <div className="space-y-2 sm:min-w-[220px]">
              <Label className="text-base">时间基准</Label>
              <Select
                value={tempRetentionBasis}
                disabled={retentionDetailLoading}
                onValueChange={(v) => setTempRetentionBasis(v as 'created_at' | 'publish_time')}
              >
                <SelectTrigger className="w-full sm:w-[220px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="created_at">入库时间 (created_at)</SelectItem>
                  <SelectItem value="publish_time">微信发布时间 (publish_time)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="shrink-0">
              <Button
                onClick={handleSaveArticleRetention}
                disabled={
                  retentionDetailLoading ||
                  retentionDetailSaving ||
                  !isRetentionDetailChanged ||
                  tempRetentionDays < 1
                }
              >
                {retentionDetailSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                保存
              </Button>
            </div>
          </div>
          <p className="text-xs text-muted-foreground max-w-xl border-l-2 border-muted pl-3">
            实际删除方式与{' '}
            <code className="text-[0.7rem]">article.true_delete</code> 一致；排程为{' '}
            <code className="text-[0.7rem]">article.retention.cron</code> 时请在配置文件中修改。若设置{' '}
            <code className="text-[0.7rem]">WERSS_ENV_OVERRIDES_DB=true</code>
            ，未在环境变量 / yaml 中留空的项才会使用此处写入数据库的值。
          </p>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1 space-y-1.5">
              <CardTitle>图片与对象存储</CardTitle>
              <CardDescription>
                单管理员部署时，控制是否在 MinIO 可用的情况下将公众号文章图片转存到自建对象存储。
              </CardDescription>
            </div>
            <Switch
              id="store-article-images"
              className="mt-1 shrink-0"
              checked={storeArticleImages}
              disabled={storeArticleImagesLoading}
              onCheckedChange={(v) => void handleStoreArticleImagesChange(v)}
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="store-article-images" className="text-base">转存公众号图片到 MinIO</Label>
            <ul className="text-sm text-muted-foreground max-w-xl list-disc space-y-1.5 pl-5">
              <li>
                <span className="font-medium text-foreground">MinIO 未启用或不可用</span>
                ：不转存；正文与封面使用微信侧图片链接。
              </li>
              <li>
                <span className="font-medium text-foreground">MinIO 可用、本开关关闭</span>
                ：不转存；仍使用微信链接（节省对象存储；外链可用性可能受上游访问策略或时效影响）。
              </li>
              <li>
                <span className="font-medium text-foreground">MinIO 可用、本开关开启</span>
                ：下载并上传到对象存储；正文与封面使用存储 URL（更稳定）。
              </li>
            </ul>
            <p className="text-xs text-muted-foreground max-w-xl border-l-2 border-muted pl-3">
              配置优先级：若设置 <code className="text-[0.7rem]">WERSS_ENV_OVERRIDES_DB=true</code>
              ，则以环境变量与 <code className="text-[0.7rem]">config.yaml</code> 为准；仅当对应键未设置或为空时，才会采用此处写入数据库的值。
            </p>
          </div>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>标签提取设置</CardTitle>
          <CardDescription>
            管理 AI 自动提取标签时使用的提示词模板。当前配置保存在数据库配置表中，保存后会直接影响后续标签提取结果。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-0.5">
            <Label className="text-base">标签提取提示词</Label>
            <p className="text-sm text-muted-foreground">
              支持占位符：<code>{'{{max_tags}}'}</code>、<code>{'{{custom_tags_hint}}'}</code>、<code>{'{{text}}'}</code>。
            </p>
          </div>
          <div className="space-y-2">
            <Label className="text-sm">预设模板</Label>
            <Select value={tagPromptPreset} onValueChange={handleTagPromptPresetChange}>
              <SelectTrigger className="w-[220px]">
                <SelectValue placeholder="选择提示词模板" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="tech">科技</SelectItem>
                <SelectItem value="medical">医学</SelectItem>
                <SelectItem value="legal">法律</SelectItem>
                <SelectItem value="custom">自定义</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              选择预设后会直接填充到下方编辑框；如果你手动修改内容，保存后会自动识别为“自定义”或对应预设。
            </p>
          </div>
          <Textarea
            ref={tagPromptTextareaRef}
            value={tempTagPrompt}
            onChange={(e) => {
              const value = e.target.value
              setTempTagPrompt(value)
              setTagPromptPreset(detectTagPromptPreset(value))
            }}
            className="min-h-[320px] font-mono text-sm"
            disabled={tagPromptLoading}
          />
          <div className="flex items-center gap-2">
            <Button
              onClick={handleSaveTagPrompt}
              disabled={tagPromptLoading || !isTagPromptChanged || !tempTagPrompt.trim()}
            >
              {tagPromptLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              保存提示词
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setTempTagPrompt(DEFAULT_TAG_EXTRACT_PROMPT)
                setTagPromptPreset('tech')
              }}
              disabled={tagPromptLoading}
            >
              恢复科技默认
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Settings
