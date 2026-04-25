import * as React from "react"
import { cn } from "@/lib/utils"

interface StatisticProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: React.ReactNode
  value: React.ReactNode
  prefix?: React.ReactNode
  suffix?: React.ReactNode
}

const Statistic = React.forwardRef<HTMLDivElement, StatisticProps>(
  ({ className, title, value, prefix, suffix, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("flex flex-col", className)}
        {...props}
      >
        {title && (
          <div className="text-sm text-muted-foreground mb-1">{title}</div>
        )}
        <div className="flex items-baseline gap-1">
          {prefix && <span className="text-muted-foreground">{prefix}</span>}
          <span className="text-2xl font-semibold">{value}</span>
          {suffix && <span className="text-muted-foreground">{suffix}</span>}
        </div>
      </div>
    )
  }
)
Statistic.displayName = "Statistic"

export { Statistic }
