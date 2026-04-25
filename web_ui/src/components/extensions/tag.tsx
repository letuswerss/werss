import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const tagVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        green: "border-transparent bg-green-500 text-white hover:bg-green-600",
        red: "border-transparent bg-red-500 text-white hover:bg-red-600",
        gray: "border-transparent bg-gray-500 text-white hover:bg-gray-600",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface TagProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof tagVariants> {
  color?: "green" | "red" | "gray" | "default"
}

const Tag = React.forwardRef<HTMLDivElement, TagProps>(
  ({ className, variant, color, ...props }, ref) => {
    const finalVariant = color || variant
    return (
      <div
        ref={ref}
        className={cn(tagVariants({ variant: finalVariant }), className)}
        {...props}
      />
    )
  }
)
Tag.displayName = "Tag"

export { Tag, tagVariants }
