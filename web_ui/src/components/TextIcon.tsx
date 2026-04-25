import React, { useEffect, useRef } from 'react'

interface TextIconProps {
  text: string
  iconClass: string
  backgroundColor?: string
  textColor?: string
}

const TextIcon: React.FC<TextIconProps> = ({
  text,
  iconClass,
  backgroundColor = '#fff',
  textColor = '#ff0000'
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const letter = text.charAt(0).toUpperCase()

    // 设置画布大小
    canvas.width = 24
    canvas.height = 24

    // 绘制背景
    ctx.fillStyle = backgroundColor
    ctx.beginPath()
    ctx.arc(12, 12, 10, 0, Math.PI * 2)
    ctx.fill()

    // 绘制字母
    ctx.fillStyle = textColor
    ctx.font = 'bold 14px Arial'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(letter, 12, 12)
  }, [text, backgroundColor, textColor])

  return (
    <span className="inline-flex items-center gap-2">
      <i className={iconClass}></i>
      <canvas ref={canvasRef} className="w-6 h-6 rounded-full"></canvas>
    </span>
  )
}

export default TextIcon

