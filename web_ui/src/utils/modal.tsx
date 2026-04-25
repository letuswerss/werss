import React, { useState } from "react"
import { createRoot } from "react-dom/client"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

let modalContainer: HTMLElement | null = null

const createModalContainer = () => {
  if (!modalContainer) {
    modalContainer = document.createElement("div")
    document.body.appendChild(modalContainer)
  }
  return modalContainer
}

// 内部组件，用于管理对话框状态
const ConfirmDialog: React.FC<{
  title?: string
  content?: React.ReactNode
  onOk?: () => void | Promise<void>
  onCancel?: () => void
  okText?: string
  cancelText?: string
  onClose: () => void
}> = ({ title, content, onOk, onCancel, okText, cancelText, onClose }) => {
  const [isOpen, setIsOpen] = useState(true)

  const handleClose = () => {
    setIsOpen(false)
    // 延迟移除容器，让关闭动画完成
    setTimeout(() => {
      onClose()
    }, 200)
  }

  const handleOk = async () => {
    if (onOk) {
      await onOk()
    }
    handleClose()
  }

  const handleCancel = () => {
    if (onCancel) {
      onCancel()
    }
    handleClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title || "确认"}</DialogTitle>
          {content && (
            <DialogDescription>{content}</DialogDescription>
          )}
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={handleCancel}>
            {cancelText || "取消"}
          </Button>
          <Button onClick={handleOk}>
            {okText || "确认"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export const Modal = {
  confirm: (options: {
    title?: string
    content?: React.ReactNode
    onOk?: () => void | Promise<void>
    onCancel?: () => void
    okText?: string
    cancelText?: string
  }) => {
    const container = createModalContainer()

    const handleClose = () => {
      if (container && container.parentNode) {
        container.parentNode.removeChild(container)
      }
      modalContainer = null
    }

    const root = createRoot(container)
    root.render(
      <ConfirmDialog
        title={options.title}
        content={options.content}
        onOk={options.onOk}
        onCancel={options.onCancel}
        okText={options.okText}
        cancelText={options.cancelText}
        onClose={handleClose}
      />
    )
  },
}
