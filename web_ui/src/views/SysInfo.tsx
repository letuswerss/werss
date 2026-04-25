import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { getSysInfo } from '@/api/sysInfo'
import SystemResources from '@/components/SystemResources'
import { Monitor, Code, Clock, Cpu, Key, PlayCircle, Package, Download } from 'lucide-react'

interface SysInfo {
  version: string
  os: {
    name: string
    version: string
    release: string
  }
  python_version: string
  uptime: number
  system: {
    node: string
    machine: string
    processor: string
  }
  api_version: string
  core_version: string
  latest_version: string
  need_update: boolean
  wx: {
    token: string
    expiry_time: string
    login: boolean
  }
  queue: {
    is_running: boolean
    pending_tasks: number
  }
  article?: {
    mp_all_count: number
    all_count: number
    no_content_count: number
    has_content_count: number
    wrong_count: number
  }
  resources?: any
}

const SysInfo: React.FC = () => {
  const { t } = useTranslation()
  const [sysInfo, setSysInfo] = useState<SysInfo>({
    version: '',
    os: {
      name: '',
      version: '',
      release: ''
    },
    python_version: '',
    uptime: 0,
    system: {
      node: '',
      machine: '',
      processor: ''
    },
    api_version: '/api/v1/wx',
    core_version: '',
    latest_version: '',
    need_update: true,
    wx: {
      token: '',
      expiry_time: '',
      login: false
    },
    queue: {
      is_running: false,
      pending_tasks: 0
    }
  })

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return t('sysInfoPage.uptime', { days, hours, minutes })
  }

  const openUpdateLink = () => {
    // 更新链接已移除
  }

  useEffect(() => {
    const fetchSysInfo = async () => {
      const data = await getSysInfo()
      setSysInfo(data)
    }
    fetchSysInfo()
  }, [])

  const InfoItem = ({ icon: Icon, label, value }: { icon: any, label: string, value: string | number | React.ReactNode }) => (
    <div className="flex items-start gap-3 py-3 border-b last:border-0">
      <Icon className="h-5 w-5 text-muted-foreground mt-0.5" />
      <div className="flex-1">
        <div className="text-sm font-medium text-muted-foreground mb-1">{label}</div>
        <div className="text-base">{value}</div>
      </div>
    </div>
  )

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 text-foreground">
          {t('layout.sysInfo')}
        </h1>
        <p className="text-muted-foreground text-sm">
          {t('sysInfoPage.versionLine', { version: sysInfo.version || '0.1' })}
        </p>
      </div>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>{t('sysInfoPage.cardResources')}</CardTitle>
        </CardHeader>
        <CardContent>
          <SystemResources />
        </CardContent>
      </Card>

      {sysInfo.article && (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>{t('sysInfoPage.cardArticleStats')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InfoItem icon={Package} label={t('sysInfoPage.articleMpTotal')} value={sysInfo.article.mp_all_count || 0} />
              <InfoItem icon={Package} label={t('sysInfoPage.articleTotal')} value={sysInfo.article.all_count || 0} />
              <InfoItem icon={Package} label={t('sysInfoPage.articleNoContent')} value={sysInfo.article.no_content_count || 0} />
              <InfoItem icon={Package} label={t('sysInfoPage.articleHasContent')} value={sysInfo.article.has_content_count || 0} />
              <InfoItem icon={Package} label={t('sysInfoPage.articleDeleted')} value={sysInfo.article.wrong_count || 0} />
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t('sysInfoPage.cardRuntime')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-0">
            <InfoItem icon={Monitor} label={t('sysInfoPage.runtimeOs')} value={sysInfo.os.name} />
            <InfoItem icon={Code} label={t('sysInfoPage.runtimeOsVersion')} value={`${sysInfo.os.version} (${sysInfo.os.release})`} />
            <InfoItem icon={Code} label={t('sysInfoPage.runtimePython')} value={sysInfo.python_version} />
            <InfoItem icon={Clock} label={t('sysInfoPage.runtimeUptime')} value={formatUptime(sysInfo.uptime)} />
            <InfoItem icon={Cpu} label={t('sysInfoPage.runtimeArch')} value={`${sysInfo.system.node} / ${sysInfo.system.machine} (${sysInfo.system.processor})`} />
            <InfoItem icon={Key} label={t('sysInfoPage.runtimeToken')} value={sysInfo.wx.token} />
            <InfoItem
              icon={Key}
              label={t('sysInfoPage.runtimeExpiry')}
              value={!sysInfo.wx.login ? t('sysInfoPage.notLoggedIn') : sysInfo.wx.expiry_time}
            />
            <InfoItem icon={Key} label={t('sysInfoPage.runtimeApiVersion')} value={sysInfo.api_version} />
            <InfoItem
              icon={PlayCircle}
              label={t('sysInfoPage.runtimeQueue')}
              value={sysInfo.queue.is_running ? t('sysInfoPage.queueRunning') : t('sysInfoPage.queueStopped')}
            />
            <InfoItem icon={PlayCircle} label={t('sysInfoPage.runtimeQueuePending')} value={sysInfo.queue.pending_tasks || 0} />
            <InfoItem icon={Package} label={t('sysInfoPage.runtimeCoreVersion')} value={sysInfo.core_version} />
            <div className="flex items-start gap-3 py-3 border-b last:border-0">
              <Download className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="flex-1">
                <div className="text-sm font-medium text-muted-foreground mb-1">{t('sysInfoPage.latestVersion')}</div>
                <div className="flex items-center gap-2">
                  <span className="text-base">{sysInfo.latest_version}</span>
                  {sysInfo.need_update && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={openUpdateLink}
                    >
                      {t('sysInfoPage.updateNow')}
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default SysInfo
