import * as React from "react"
import { cn } from "@/lib/utils"

export interface DescriptionsProps extends React.HTMLAttributes<HTMLDivElement> {
  bordered?: boolean
  column?: number | { xs?: number; sm?: number; md?: number; lg?: number }
}

const Descriptions = React.forwardRef<HTMLDivElement, DescriptionsProps>(
  ({ className, bordered = false, column = 3, ...props }, ref) => {
    const getColumnClass = () => {
      if (typeof column === "number") {
        return `grid-cols-${column}`
      }
      return `grid-cols-1 sm:grid-cols-${column.sm || 2} md:grid-cols-${column.md || 2} lg:grid-cols-${column.lg || 3}`
    }

    return (
      <div
        ref={ref}
        className={cn(
          "grid gap-4",
          getColumnClass(),
          bordered && "divide-y divide-border",
          className
        )}
        {...props}
      />
    )
  }
)
Descriptions.displayName = "Descriptions"

const DescriptionsItem = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    label?: React.ReactNode
  }
>(({ className, label, children, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "flex flex-col space-y-1",
        className
      )}
      {...props}
    >
      {label && (
        <div className="text-sm font-medium text-muted-foreground">{label}</div>
      )}
      <div className="text-sm">{children}</div>
    </div>
  )
})
DescriptionsItem.displayName = "DescriptionsItem"

export { Descriptions, DescriptionsItem }
