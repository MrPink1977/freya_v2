import { useEffect, useState } from 'react'

function VolumeMeter({ level, active }) {
  const [bars, setBars] = useState([])

  // Convert 0-100 level to bar count (12 bars total)
  useEffect(() => {
    const barCount = 12
    const activeBars = Math.ceil((level / 100) * barCount)

    const newBars = Array.from({ length: barCount }, (_, i) => {
      const isActive = i < activeBars
      const intensity = i / barCount

      return {
        id: i,
        active: isActive,
        color: getBarColor(intensity, isActive)
      }
    })

    setBars(newBars)
  }, [level])

  const getBarColor = (intensity, isActive) => {
    if (!isActive) return 'var(--bg-tertiary)'

    // Green -> Yellow -> Red gradient
    if (intensity < 0.6) return 'var(--success)'
    if (intensity < 0.85) return 'var(--warning)'
    return 'var(--error)'
  }

  return (
    <div className="volume-meter">
      <div className="volume-label">
        <span>Level</span>
        <span className="volume-value">{Math.round(level)}%</span>
      </div>
      <div className="volume-bars">
        {bars.map(bar => (
          <div
            key={bar.id}
            className={`volume-bar ${bar.active ? 'active' : ''}`}
            style={{
              backgroundColor: bar.color,
              opacity: bar.active ? 1 : 0.3
            }}
          />
        ))}
      </div>
      {!active && (
        <div className="volume-inactive">
          <span>Inactive</span>
        </div>
      )}
    </div>
  )
}

export default VolumeMeter
