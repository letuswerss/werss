import { toast } from "@/hooks/use-toast"

export const Message = {
  success: (content: string) => {
    toast({
      title: "成功",
      description: content,
      variant: "default",
    })
  },
  error: (content: string) => {
    toast({
      title: "错误",
      description: content,
      variant: "destructive",
    })
  },
  warning: (content: string) => {
    toast({
      title: "警告",
      description: content,
      variant: "default",
    })
  },
  info: (content: string) => {
    toast({
      title: "提示",
      description: content,
      variant: "default",
    })
  },
}
