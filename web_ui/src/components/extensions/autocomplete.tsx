import * as React from "react"
import { cn } from "@/lib/utils"

interface AutoCompleteProps extends Omit<React.ComponentProps<"input">, "onChange" | "onSelect"> {
  data?: Array<{ value: string; name?: string }>
  onSelect?: (value: string) => void
  onSearch?: (value: string) => void
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
}

const AutoComplete = React.forwardRef<HTMLInputElement, AutoCompleteProps>(
  ({ className, data = [], onSelect, onSearch, onChange, value, ...props }, ref) => {
    const [open, setOpen] = React.useState(false)
    const [filteredData, setFilteredData] = React.useState(data)
    const [inputValue, setInputValue] = React.useState(value || '')

    React.useEffect(() => {
      if (value !== undefined) {
        setInputValue(value)
      }
    }, [value])

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value
      setInputValue(newValue)
      
      if (onSearch) {
        onSearch(newValue)
      }
      if (onChange) {
        onChange(e)
      }
      if (newValue) {
        const filtered = data.filter(
          (item) =>
            item.value.toLowerCase().includes(newValue.toLowerCase()) ||
            item.name?.toLowerCase().includes(newValue.toLowerCase())
        )
        setFilteredData(filtered)
        setOpen(true)
      } else {
        setFilteredData(data)
        setOpen(false)
      }
    }

    const handleSelect = (selectedValue: string) => {
      setInputValue(selectedValue)
      if (onSelect) {
        onSelect(selectedValue)
      }
      // 触发 onChange 事件
      if (onChange) {
        const syntheticEvent = {
          target: { value: selectedValue }
        } as React.ChangeEvent<HTMLInputElement>
        onChange(syntheticEvent)
      }
      setOpen(false)
    }

    React.useEffect(() => {
      setFilteredData(data)
    }, [data])

    return (
      <div className="relative">
        <input
          ref={ref}
          className={cn(
            "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
            className
          )}
          value={inputValue}
          onChange={handleChange}
          onFocus={() => {
            if (filteredData.length > 0) setOpen(true)
          }}
          onBlur={() => {
            setTimeout(() => setOpen(false), 200)
          }}
          {...props}
        />
        {open && filteredData.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-popover border rounded-md shadow-md max-h-60 overflow-auto">
            {filteredData.map((item, index) => (
              <div
                key={index}
                className="px-3 py-2 cursor-pointer hover:bg-accent hover:text-accent-foreground"
                onMouseDown={(e) => {
                  e.preventDefault()
                  handleSelect(item.value)
                }}
              >
                {item.name || item.value}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }
)
AutoComplete.displayName = "AutoComplete"

export { AutoComplete }

