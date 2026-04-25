import React, { useMemo } from 'react'

interface CustomPieChartProps {
  percent: number
  size?: number
  title?: string
  info?: string
}

const CustomPieChart: React.FC<CustomPieChartProps> = ({
  percent = 0,
  size = 150,
  title = '',
  info = ''
}) => {
  const dashArray = useMemo(() => {
    const circumference = 2 * Math.PI * 40
    const progress = (percent / 100) * circumference
    return `${progress} ${circumference}`
  }, [percent])

  const strokeColor = useMemo(() => {
    const startColor = { r: 32, g: 165, b: 58 }
    const endColor = { r: 245, g: 34, b: 45 }
    const ratio = percent / 100
    const r = Math.floor(startColor.r + (endColor.r - startColor.r) * ratio)
    const g = Math.floor(startColor.g + (endColor.g - startColor.g) * ratio)
    const b = Math.floor(startColor.b + (endColor.b - startColor.b) * ratio)
    return `rgb(${r}, ${g}, ${b})`
  }, [percent])

  return (
    <div className="inline-block">
      <svg width={size} height={size} viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke="#f0f0f0"
          strokeWidth="3"
        />
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke={strokeColor}
          strokeWidth="5"
          strokeDasharray={dashArray}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
        />
        <text x="50" y="30" textAnchor="middle" dominantBaseline="middle" fontSize="12" fill="#333">
          {title}
        </text>
        <text x="50" y="50" textAnchor="middle" dominantBaseline="middle" fontSize="18" fill={strokeColor} fontWeight="bold">
          {percent}%
        </text>
        <text x="50" y="70" textAnchor="middle" dominantBaseline="middle" fontSize="6" fill="#666">
          {info}
        </text>
      </svg>
    </div>
  )
}

export default CustomPieChart
