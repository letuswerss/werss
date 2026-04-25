import * as React from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface ButtonGroupProps {
  value: string
  onValueChange: (value: string) => void
  options: Array<{ value: string; label: string }>
  size?: "default" | "sm"
  className?: string
}

const ButtonGroup = React.forwardRef<HTMLDivElement, ButtonGroupProps>(
  ({ value, onValueChange, options, size = "default", className }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("inline-flex gap-0.5 rounded-lg border border-input bg-background p-0.5", className)}
        role="group"
      >
        {options.map((option) => {
          const isSelected = value === option.value
          return (
            <Button
              key={option.value}
              type="button"
              variant={isSelected ? "default" : "ghost"}
              size={size === "sm" ? "sm" : "default"}
              onClick={() => onValueChange(option.value)}
              className={cn(
                "h-7 min-w-[50px] rounded-md px-2.5 text-xs transition-colors",
                isSelected 
                  ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm" 
                  : "hover:bg-accent hover:text-accent-foreground"
              )}
            >
              {option.label}
            </Button>
          )
        })}
      </div>
    )
  }
)
ButtonGroup.displayName = "ButtonGroup"

export { ButtonGroup }

