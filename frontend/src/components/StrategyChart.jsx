import React, { useEffect, useRef } from 'react'

const StrategyChart = ({ weights, threatIndex }) => {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const width = canvas.width
    const height = canvas.height

    // Clear
    ctx.clearRect(0, 0, width, height)

    // Background (transparent)
    ctx.fillStyle = 'rgba(15, 23, 42, 0.3)' // slate-900/30
    ctx.fillRect(0, 0, width, height)

    // Chart title
    ctx.fillStyle = 'rgba(255,255,255,0.7)'
    ctx.font = '600 13px Inter, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('Nash Equilibrium Strategy Weights', width / 2, 28)

    // Dimensions
    const barWidth = 70
    const gap = 50
    const startX = (width - (barWidth * 3 + gap * 2)) / 2
    const bottomY = height - 50
    const maxHeight = height - 80

    const strategies = ['Linguistic', 'Behavioral', 'Acoustic']
    const colors = ['#06b6d4', '#10b981', '#a855f7'] // cyan, emerald, purple
    const values = [
      weights?.linguistic || 0.33,
      weights?.behavioral || 0.33,
      weights?.acoustic || 0.33
    ]

    // Draw bars with gradient and shadow
    strategies.forEach((strategy, index) => {
      const x = startX + index * (barWidth + gap)
      const barHeight = values[index] * maxHeight
      const y = bottomY - barHeight

      // Shadow
      ctx.shadowColor = 'rgba(0,0,0,0.3)'
      ctx.shadowBlur = 12
      ctx.shadowOffsetY = 4

      // Gradient
      const grad = ctx.createLinearGradient(x, y, x, bottomY)
      const color = colors[index]
      grad.addColorStop(0, color)
      grad.addColorStop(1, color + '66')
      ctx.fillStyle = grad

      // Rounded rectangle
      const radius = 6
      ctx.beginPath()
      ctx.moveTo(x + radius, y)
      ctx.lineTo(x + barWidth - radius, y)
      ctx.quadraticCurveTo(x + barWidth, y, x + barWidth, y + radius)
      ctx.lineTo(x + barWidth, bottomY)
      ctx.lineTo(x, bottomY)
      ctx.lineTo(x, y + radius)
      ctx.quadraticCurveTo(x, y, x + radius, y)
      ctx.closePath()
      ctx.fill()

      // Reset shadow
      ctx.shadowBlur = 0

      // Value text
      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 13px Inter, sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(
        `${(values[index] * 100).toFixed(0)}%`,
        x + barWidth / 2,
        y - 10
      )

      // Label
      ctx.fillStyle = 'rgba(255,255,255,0.5)'
      ctx.font = '11px Inter, sans-serif'
      ctx.fillText(strategy, x + barWidth / 2, bottomY + 20)
    })

    // Threat index indicator
    if (threatIndex !== undefined) {
      const threatX = width - 140
      const threatY = 20
      ctx.fillStyle = 'rgba(239, 68, 68, 0.15)'
      ctx.roundRect(threatX, threatY, 120, 24, 12)
      ctx.fill()

      ctx.fillStyle = '#f87171'
      ctx.font = '11px Inter, sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(`⚠️ Threat: ${(threatIndex * 100).toFixed(1)}%`, threatX + 12, threatY + 16)
    }

    // Add a subtle grid line at bottom
    ctx.strokeStyle = 'rgba(255,255,255,0.05)'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(30, bottomY)
    ctx.lineTo(width - 30, bottomY)
    ctx.stroke()

  }, [weights, threatIndex])

  return (
    <div className="glass-card p-4">
      <canvas
        ref={canvasRef}
        width={600}
        height={280}
        className="w-full h-auto rounded-xl"
      />
    </div>
  )
}

export default StrategyChart