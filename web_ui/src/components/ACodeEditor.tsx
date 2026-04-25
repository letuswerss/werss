import React, { lazy, Suspense } from 'react'

// 动态导入 Monaco Editor（体积较大，约 2-3MB）
const Editor = lazy(() => import('@monaco-editor/react'))

interface ACodeEditorProps {
  value?: string
  language?: string
  placeholder?: string
  height?: string
  onChange?: (value: string) => void
}

const ACodeEditor: React.FC<ACodeEditorProps> = ({
  value = '',
  language = 'plaintext',
  placeholder = '',
  height = '200px',
  onChange
}) => {
  return (
    <div className="w-full min-w-[500px] border border-[var(--color-border)] rounded">
      <Suspense fallback={
        <div className="flex items-center justify-center" style={{ height }}>
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
        </div>
      }>
      <Editor
        height={height}
        language={language === 'custom' ? 'plaintext' : language}
        value={value}
        onChange={(val: string | undefined) => onChange?.(val || '')}
        theme={language === 'custom' ? 'vs' : 'vs'}
        options={{
          minimap: { enabled: false },
          automaticLayout: true,
          scrollBeyondLastLine: false,
          fontSize: 14,
          lineNumbers: 'on' as const,
          roundedSelection: true,
          scrollbar: {
            vertical: 'auto' as const,
            horizontal: 'hidden' as const
          },
          wordWrap: 'on' as const,
          placeholder: placeholder
        }}
      />
      </Suspense>
    </div>
  )
}

export default ACodeEditor
