import { useTheme } from "@/store"
import { Toaster as Sonner } from "sonner"

type ToasterProps = React.ComponentProps<typeof Sonner>

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-background group-[.toaster]:text-foreground group-[.toaster]:border-border group-[.toaster]:shadow-lg group-[.toaster]:rounded-xl",
          description: "group-[.toast]:text-muted-foreground",
          actionButton:
            "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
          cancelButton:
            "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground",
          success: "group-[.toast]:bg-emerald-500/10 group-[.toast]:text-emerald-700 dark:group-[.toast]:text-emerald-400 group-[.toast]:border-emerald-500/30",
          error: "group-[.toast]:bg-red-500/10 group-[.toast]:text-red-700 dark:group-[.toast]:text-red-400 group-[.toast]:border-red-500/30",
          warning: "group-[.toast]:bg-amber-500/10 group-[.toast]:text-amber-700 dark:group-[.toast]:text-amber-400 group-[.toast]:border-amber-500/30",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
