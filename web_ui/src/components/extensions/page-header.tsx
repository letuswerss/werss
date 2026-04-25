import * as React from "react"
import { ArrowLeft } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

interface PageHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string
  subTitle?: string
  onBack?: () => void
  extra?: React.ReactNode
}

const PageHeader = React.forwardRef<HTMLDivElement, PageHeaderProps>(
  ({ className, title, subTitle, onBack, extra, ...props }, ref) => {
    const navigate = useNavigate()
    
    const handleBack = () => {
      if (onBack) {
        onBack()
      } else {
        navigate(-1)
      }
    }

    return (
      <div
        ref={ref}
        className={cn("mb-6", className)}
        {...props}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {onBack !== null && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleBack}
                className="h-8 w-8"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
            )}
            <div>
              <h1 className="text-2xl font-bold">{title}</h1>
              {subTitle && (
                <p className="text-sm text-muted-foreground mt-1">{subTitle}</p>
              )}
            </div>
          </div>
          {extra && <div>{extra}</div>}
        </div>
      </div>
    )
  }
)
PageHeader.displayName = "PageHeader"

export { PageHeader }

