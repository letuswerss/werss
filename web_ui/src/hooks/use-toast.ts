"use client"

import { toast as sonnerToast } from "sonner"
import type { ToastProps } from "@/components/ui/toast"

type Toast = ToastProps & {
  title?: React.ReactNode
  description?: React.ReactNode
  variant?: "default" | "destructive" | "success" | "warning"
}

function toast({ title, description, variant, ...props }: Toast) {
  const options = {
    description: description,
    ...props,
  }

  let id: string | number = ""

  switch (variant) {
    case "success":
      id = sonnerToast.success(title, options)
      break
    case "destructive":
      id = sonnerToast.error(title, options)
      break
    case "warning":
      id = sonnerToast.warning(title, options)
      break
    default:
      id = sonnerToast(title, options)
      break
  }

  return {
    id,
    dismiss: () => sonnerToast.dismiss(id),
    update: (props: Toast) => {
        // Sonner update logic if needed
    }
  }
}

function useToast() {
  return {
    toast,
    dismiss: (toastId?: string | number) => sonnerToast.dismiss(toastId),
  }
}

export { useToast, toast }
