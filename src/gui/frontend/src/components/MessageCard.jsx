import { useState } from 'react'

function MessageCard({ message }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [copied, setCopied] = useState(false)

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    const date = new Date(timestamp)
    return date.toLocaleTimeString() + '.' + date.getMilliseconds().toString().padStart(3, '0')
  }

  const getChannelColor = (channel) => {
    if (!channel) return '#94a3b8'

    // Hash channel name to get consistent color
    let hash = 0
    for (let i = 0; i < channel.length; i++) {
      hash = channel.charCodeAt(i) + ((hash << 5) - hash)
    }

    const colors = [
      '#3b82f6', // blue
      '#8b5cf6', // purple
      '#ec4899', // pink
      '#f59e0b', // amber
      '#10b981', // emerald
      '#06b6d4', // cyan
    ]

    return colors[Math.abs(hash) % colors.length]
  }

  const handleCopy = () => {
    const text = JSON.stringify(message, null, 2)
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const renderMessageData = (data) => {
    if (typeof data === 'string') {
      return <span className="message-string">{data}</span>
    }

    if (typeof data === 'object' && data !== null) {
      return (
        <pre className="message-json">
          {JSON.stringify(data, null, 2)}
        </pre>
      )
    }

    return <span className="message-primitive">{String(data)}</span>
  }

  const channelColor = getChannelColor(message.channel)

  return (
    <div className="message-card">
      <div className="message-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="message-channel-info">
          <div
            className="channel-dot"
            style={{ backgroundColor: channelColor }}
          />
          <span className="channel-name">{message.channel || 'unknown'}</span>
          <span className="message-timestamp">
            {formatTimestamp(message.timestamp)}
          </span>
        </div>

        <div className="message-actions">
          <button
            className="action-button"
            onClick={(e) => {
              e.stopPropagation()
              handleCopy()
            }}
            title="Copy to clipboard"
          >
            {copied ? '✓' : '📋'}
          </button>
          <button className="expand-button">
            {isExpanded ? '▼' : '▶'}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="message-body">
          {message.message !== undefined ? (
            <div className="message-data">
              <div className="data-label">Message:</div>
              {renderMessageData(message.message)}
            </div>
          ) : (
            <div className="message-data">
              <div className="data-label">Data:</div>
              {renderMessageData(message.data || message)}
            </div>
          )}

          {/* Show raw JSON for debugging */}
          {Object.keys(message).length > 3 && (
            <details className="raw-data">
              <summary>Raw Data</summary>
              <pre>{JSON.stringify(message, null, 2)}</pre>
            </details>
          )}
        </div>
      )}
    </div>
  )
}

export default MessageCard
