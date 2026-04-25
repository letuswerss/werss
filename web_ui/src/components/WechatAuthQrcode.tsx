import { useState, useImperativeHandle, forwardRef } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2 } from 'lucide-react'
import { QRCode, checkQRCodeStatus } from '@/api/auth'

interface WechatAuthQrcodeProps {
  onSuccess?: (data: any) => void
  onError?: (error: any) => void
}

export interface WechatAuthQrcodeRef {
  startAuth: () => Promise<void>
}

const MAX_QR_IMG_RETRY = 40

const WechatAuthQrcode = forwardRef<WechatAuthQrcodeRef, WechatAuthQrcodeProps>(({ onSuccess, onError }, ref) => {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [qrcodeUrl, setQrcodeUrl] = useState('')
  const [imgRetry, setImgRetry] = useState(0)
  const [errorMessage, setErrorMessage] = useState('')

  const startAuth = async () => {
    try {
      setOpen(true)
      setLoading(true)
      setErrorMessage('')
      setImgRetry(0)

      // 获取二维码
      const res = await QRCode() as { code: string }
      setQrcodeUrl(res?.code || '')
      setLoading(false)

      // 开始检查授权状态
      checkQRCodeStatus()
        .then((statusRes) => {
          if ((statusRes as { login_status: boolean }).login_status) {
            // Message.success('授权成功')
            onSuccess?.(statusRes)
            setOpen(false)
          }
        })
        .catch((err) => {
          console.error('检查二维码状态失败:', err)
          setErrorMessage('授权失败，请重试')
          onError?.(err)
        })
    } catch (err) {
      setLoading(false)
      setErrorMessage('获取二维码失败，请重试')
      onError?.(err)
    }
  }

  useImperativeHandle(ref, () => ({
    startAuth
  }))

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>微信授权</DialogTitle>
          <DialogDescription>使用微信扫码完成授权</DialogDescription>
        </DialogHeader>
        <div className="flex flex-col items-center p-5">
          {loading && (
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="h-8 w-8 animate-spin" />
              <p>正在获取二维码...</p>
            </div>
          )}
          {!loading && qrcodeUrl && (
            <div className="flex flex-col items-center gap-4 text-center">
              <img
                src={`${qrcodeUrl}${qrcodeUrl.includes('?') ? '&' : '?'}_retry=${imgRetry}`}
                alt="微信授权二维码"
                className="w-[200px] h-[200px]"
                onError={() => {
                  if (imgRetry < MAX_QR_IMG_RETRY) {
                    window.setTimeout(() => setImgRetry((n) => n + 1), 600)
                  }
                }}
              />
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <p>请使用微信扫码授权</p>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>扫码请选择公众号或者服务号，如果没有帐号，请点击下方注册</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <p>
                如果提示没有可用帐号码，请点此
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <a 
                        href="https://mp.weixin.qq.com/cgi-bin/registermidpage?action=index&weblogo=1&lang=zh_CN" 
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary underline ml-1"
                      >
                        注册
                      </a>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>注册时请选择公众号或者服务号</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </p>
            </div>
          )}
          {!loading && !qrcodeUrl && errorMessage && (
            <div className="flex flex-col items-center gap-4">
              <Alert variant="destructive">
                <AlertDescription>{errorMessage}</AlertDescription>
              </Alert>
              <Button onClick={startAuth}>重试</Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
})

WechatAuthQrcode.displayName = 'WechatAuthQrcode'

export default WechatAuthQrcode
