"use client"

import * as React from "react"
import * as DialogPrimitive from "@radix-ui/react-dialog"
import { X } from "lucide-react"

import { cn } from "@/lib/utils"

const Dialog = DialogPrimitive.Root

const DialogTrigger = DialogPrimitive.Trigger

const DialogPortal = DialogPrimitive.Portal

const DialogClose = DialogPrimitive.Close

const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    )}
    {...props}
  />
))
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName

type DialogContentProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> & {
  /**
   * 提供可见的 DialogTitle 时无需设置；若调用方未在 children 中放置 DialogTitle，
   * 默认会渲染一个 sr-only 的标题，避免 Radix 在控制台报
   * "DialogContent requires a DialogTitle" 警告。
   */
  srOnlyTitle?: string
  /**
   * 与 srOnlyTitle 类似：当未显式提供 DialogDescription 时，可传入这里以满足无障碍要求。
   * 若不需要描述，请显式传入 aria-describedby={undefined} 来抑制 Radix 的描述警告。
   */
  srOnlyDescription?: string
}

const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  DialogContentProps
>(({ className, children, srOnlyTitle = "对话框", srOnlyDescription, ...props }, ref) => {
  const hasTitle = React.useMemo(
    () => containsComponent(children, DialogPrimitive.Title),
    [children],
  )
  const hasDescription = React.useMemo(
    () => containsComponent(children, DialogPrimitive.Description),
    [children],
  )

  return (
    <DialogPortal>
      <DialogOverlay />
      <DialogPrimitive.Content
        ref={ref}
        className={cn(
          "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg",
          className
        )}
        {...(hasDescription || srOnlyDescription
          ? {}
          : { "aria-describedby": undefined })}
        {...props}
      >
        {hasTitle ? null : (
          <DialogPrimitive.Title className="sr-only">{srOnlyTitle}</DialogPrimitive.Title>
        )}
        {hasDescription || !srOnlyDescription ? null : (
          <DialogPrimitive.Description className="sr-only">
            {srOnlyDescription}
          </DialogPrimitive.Description>
        )}
        {children}
        <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </DialogPortal>
  )
})
DialogContent.displayName = DialogPrimitive.Content.displayName

/**
 * 递归判断 children 中是否包含指定 Radix 组件（如 DialogPrimitive.Title）。
 * 用来决定是否需要补一个 sr-only 占位，避免 Radix 控制台警告。
 * 同时通过 displayName 匹配 forwardRef 包装的同名导出（DialogTitle、DialogDescription 等）。
 */
function containsComponent(
  children: React.ReactNode,
  target: React.ElementType & { displayName?: string },
): boolean {
  const targetName = target.displayName
  let found = false
  React.Children.forEach(children, (child) => {
    if (found || !React.isValidElement(child)) return
    const childType = child.type as (React.ElementType & { displayName?: string }) | undefined
    if (
      childType === target ||
      (targetName && (childType as { displayName?: string } | undefined)?.displayName === targetName)
    ) {
      found = true
      return
    }
    const inner = (child.props as { children?: React.ReactNode })?.children
    if (inner && containsComponent(inner, target)) {
      found = true
    }
  })
  return found
}

const DialogHeader = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex flex-col space-y-1.5 text-center sm:text-left",
      className
    )}
    {...props}
  />
)
DialogHeader.displayName = "DialogHeader"

const DialogFooter = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2",
      className
    )}
    {...props}
  />
)
DialogFooter.displayName = "DialogFooter"

const DialogTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn(
      "text-lg font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
DialogTitle.displayName = DialogPrimitive.Title.displayName

const DialogDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
DialogDescription.displayName = DialogPrimitive.Description.displayName

export {
  Dialog,
  DialogPortal,
  DialogOverlay,
  DialogClose,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
}
