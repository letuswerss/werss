import * as React from "react"
import { useRef } from "react"
import { Upload as UploadIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

interface UploadProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  customRequest?: (fileList: File[]) => void | Promise<void>
  fileList?: any[]
  showUploadList?: boolean
  accept?: string
  limit?: number
  children?: React.ReactNode
  onChange?: (fileList: File[]) => void
}

const Upload = React.forwardRef<HTMLInputElement, UploadProps>(
  ({ 
    className, 
    customRequest, 
    fileList = [], 
    showUploadList = true,
    accept,
    limit,
    children,
    onChange,
    ...props 
  }, ref) => {
    const inputRef = useRef<HTMLInputElement>(null)
    const [internalFileList, setInternalFileList] = React.useState<File[]>([])

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || [])
      if (limit && files.length > limit) {
        files.splice(limit)
      }
      
      if (onChange) {
        onChange(files)
      }
      
      if (customRequest) {
        const result = await customRequest(files)
        if (result === false) {
          return
        }
      }
      
      setInternalFileList(files)
      
      // Reset input
      if (inputRef.current) {
        inputRef.current.value = ''
      }
    }

    const handleClick = () => {
      inputRef.current?.click()
    }

    return (
      <div className={cn("inline-block", className)}>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={!limit || limit > 1}
          onChange={handleFileChange}
          className="hidden"
          {...props}
        />
        {children ? (
          <div onClick={handleClick} className="cursor-pointer">
            {children}
          </div>
        ) : (
          <Button
            type="button"
            variant="outline"
            onClick={handleClick}
            className="cursor-pointer"
          >
            <UploadIcon className="h-4 w-4 mr-2" />
            上传文件
          </Button>
        )}
      </div>
    )
  }
)
Upload.displayName = "Upload"

export { Upload }
