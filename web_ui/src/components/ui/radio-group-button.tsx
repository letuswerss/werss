import * as React from "react"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface RadioGroupButtonProps extends React.ComponentProps<typeof RadioGroup> {
  type?: "default" | "button"
  size?: "default" | "small"
}

const RadioGroupButton = React.forwardRef<
  React.ElementRef<typeof RadioGroup>,
  RadioGroupButtonProps
>(({ className, type = "default", size = "default", ...props }, ref) => {
  if (type === "button") {
    return (
      <RadioGroup
        ref={ref}
        className={cn("inline-flex gap-1", size === "small" && "text-sm", className)}
        {...props}
      />
    )
  }
  return (
    <RadioGroup
      ref={ref}
      className={cn("grid gap-2", size === "small" && "text-sm", className)}
      {...props}
    />
  )
})
RadioGroupButton.displayName = "RadioGroupButton"

interface RadioGroupItemButtonProps extends React.ComponentProps<typeof RadioGroupItem> {
  button?: boolean
  size?: "default" | "small"
}

const RadioGroupItemButton = React.forwardRef<
  React.ElementRef<typeof RadioGroupItem>,
  RadioGroupItemButtonProps
>(({ className, button, size = "default", children, ...props }, ref) => {
  if (button) {
    return (
      <RadioGroupItem
        ref={ref}
        asChild
        {...props}
      >
        <Button
          type="button"
          variant="outline"
          size={size === "small" ? "sm" : "default"}
          className={cn(
            className,
            "data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground data-[state=checked]:border-primary"
          )}
        >
          {children}
        </Button>
      </RadioGroupItem>
    )
  }
  
  return (
    <RadioGroupItem
      ref={ref}
      className={cn(className)}
      {...props}
    >
      {children}
    </RadioGroupItem>
  )
})
RadioGroupItemButton.displayName = "RadioGroupItemButton"

// Radio component for compatibility
const Radio = React.forwardRef<
  React.ElementRef<typeof RadioGroupItem>,
  RadioGroupItemButtonProps & {
    value: string | number
  }
>(({ children, ...props }, ref) => {
  return (
    <RadioGroupItemButton ref={ref} {...props}>
      {children}
    </RadioGroupItemButton>
  )
})
Radio.displayName = "Radio"

export { RadioGroupButton as RadioGroup, RadioGroupItemButton as RadioGroupItem, Radio }

