import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import CustomPieChart from './CustomPieChart'
import { getSysResources } from '@/api/sysInfo'

interface SystemResourcesProps { }

interface Resources {
  cpu?: {
    percent: number
    cores: number
    threads: number
  }
  memory?: {
    percent: number
    total: number
    used: number
    free: number
  }
  disk?: {
    percent: number
    total: number
    used: number
    free: number
  }
}

const SystemResources: React.FC<SystemResourcesProps> = () => {
  const { t } = useTranslation()
  const [resources, setResources] = useState<Resources>({
    cpu: { percent: 0, cores: 0, threads: 0 },
    memory: { percent: 0, total: 0, used: 0, free: 0 },
    disk: { percent: 0, total: 0, used: 0, free: 0 }
  })

  const fetchResources = async () => {
    try {
      const data = await getSysResources()
      setResources(data)
    } catch (error) {
      console.error(t('sysInfoPage.fetchResourcesFailed'), error)
    }
  }

  useEffect(() => {
    fetchResources()
    const intervalId = setInterval(() => {
      fetchResources()
    }, 2000)

    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [t])

  return (
    <div className="flex justify-around items-center flex-wrap gap-5">
      <TooltipProvider>
        {/* CPU 使用率 */}
        <div className="flex flex-col items-center cursor-pointer">
          <Tooltip>
            <TooltipTrigger asChild>
              <div>
                <CustomPieChart
                  percent={resources.cpu?.percent || 0}
                  title={t('sysInfoPage.resourcesCpuTitle')}
                  info={` ${t('sysInfoPage.resourcesCpuSubtitle', { cores: resources.cpu?.cores || 0, threads: resources.cpu?.threads || 0 })}`}
                />
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {t('sysInfoPage.resourcesCpuTooltip', {
                  cores: resources.cpu?.cores || 0,
                  threads: resources.cpu?.threads || 0,
                })}
              </p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* 内存使用率 */}
        <div className="flex flex-col items-center cursor-pointer">
          <Tooltip>
            <TooltipTrigger asChild>
              <div>
                <CustomPieChart
                  percent={resources.memory?.percent || 0}
                  title={t('sysInfoPage.resourcesMemory')}
                  info={` ${t('sysInfoPage.resourcesMemorySubtitle', { used: resources.memory?.used || 0, total: resources.memory?.total || 0 })}`}
                />
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {t('sysInfoPage.resourcesMemoryTooltip', {
                  total: resources.memory?.total || 0,
                  used: resources.memory?.used || 0,
                  free: resources.memory?.free || 0,
                })}
              </p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* 磁盘使用率 */}
        <div className="flex flex-col items-center cursor-pointer">
          <Tooltip>
            <TooltipTrigger asChild>
              <div>
                <CustomPieChart
                  percent={resources.disk?.percent || 0}
                  title={t('sysInfoPage.resourcesDisk')}
                  info={` ${t('sysInfoPage.resourcesDiskSubtitle', { used: resources.disk?.used || 0, total: resources.disk?.total || 0 })} `}
                />
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {t('sysInfoPage.resourcesDiskTooltip', {
                  total: resources.disk?.total || 0,
                  used: resources.disk?.used || 0,
                  free: resources.disk?.free || 0,
                })}
              </p>
            </TooltipContent>
          </Tooltip>
        </div>
      </TooltipProvider>
    </div>
  )
}

export default SystemResources
