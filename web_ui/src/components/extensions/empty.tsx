import * as React from "react"
import { cn } from "@/lib/utils"

export interface EmptyProps extends React.HTMLAttributes<HTMLDivElement> {
  description?: React.ReactNode
  icon?: React.ReactNode
}

const Empty = React.forwardRef<HTMLDivElement, EmptyProps>(
  ({ className, description, icon, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "flex flex-col items-center justify-center py-12 text-center",
          className
        )}
        {...props}
      >
        {icon && <div className="mb-4 text-muted-foreground">{icon}</div>}
        {description && (
          <div className="text-sm text-muted-foreground">{description}</div>
        )}
      </div>
    )
  }
)
Empty.displayName = "Empty"

export { Empty }
