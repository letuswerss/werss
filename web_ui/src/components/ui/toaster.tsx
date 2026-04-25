import { useToast } from "@/hooks/use-toast"
import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/components/ui/toast"
import { CheckCircle2, AlertCircle, Info, XCircle } from "lucide-react"

export function Toaster() {
  const { toasts } = useToast()

  const getIcon = (variant?: string) => {
    switch (variant) {
      case "success":
        return <CheckCircle2 className="h-5 w-5 text-white" />
      case "destructive":
        return <XCircle className="h-5 w-5 text-white" />
      case "warning":
        return <AlertCircle className="h-5 w-5 text-white" />
      default:
        return <Info className="h-5 w-5 text-primary" />
    }
  }

  return (
    <ToastProvider>
      {toasts.map(function ({ id, title, description, action, ...props }) {
        return (
          <Toast key={id} {...props}>
            <div className="flex gap-3 items-start">
              <div className="mt-0.5">
                {getIcon(props.variant as string)}
              </div>
              <div className="grid gap-1">
                {title && <ToastTitle className="text-sm font-bold">{title}</ToastTitle>}
                {description && (
                  <ToastDescription className="text-xs opacity-90">{description}</ToastDescription>
                )}
              </div>
            </div>
            {action}
            <ToastClose />
          </Toast>
        )
      })}
      <ToastViewport />
    </ToastProvider>
  )
}
