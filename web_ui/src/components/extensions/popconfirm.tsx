import * as React from "react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"

export interface PopconfirmProps {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  title?: string
  content?: React.ReactNode
  onOk?: () => void | Promise<void>
  onCancel?: () => void
  okText?: string
  cancelText?: string
  children?: React.ReactNode
}

export function Popconfirm({
  open,
  onOpenChange,
  title = "确认",
  content,
  onOk,
  onCancel,
  okText = "确认",
  cancelText = "取消",
  children,
}: PopconfirmProps) {
  const [internalOpen, setInternalOpen] = React.useState(false)
  const isControlled = open !== undefined
  const isOpen = isControlled ? open : internalOpen

  const handleOpenChange = (newOpen: boolean) => {
    if (!isControlled) {
      setInternalOpen(newOpen)
    }
    onOpenChange?.(newOpen)
  }

  const handleOk = async () => {
    if (onOk) {
      await onOk()
    }
    handleOpenChange(false)
  }

  const handleCancel = () => {
    onCancel?.()
    handleOpenChange(false)
  }

  return (
    <AlertDialog open={isOpen} onOpenChange={handleOpenChange}>
      {children && (
        <div onClick={() => handleOpenChange(true)}>{children}</div>
      )}
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          {content && (
            <AlertDialogDescription>{content}</AlertDialogDescription>
          )}
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={handleCancel}>
            {cancelText}
          </AlertDialogCancel>
          <AlertDialogAction onClick={handleOk}>{okText}</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
