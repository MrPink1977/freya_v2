import { useState, useEffect, useRef } from 'react'
import MessageCard from './MessageCard'
import '../styles/DebugPanel.css'

const API_URL = 'http://localhost:8000'

function DebugPanel() {
  const [messages, setMessages] = useState([])
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [autoScroll, setAutoScroll] = useState(true)
  const [isPaused, setIsPaused] = useState(false)
  const messagesEndRef = useRef(null)
  const wsRef = useRef(null)

  // Fetch initial message history
  useEffect(() => {
    fetchMessageHistory()
  }, [])

  // WebSocket for real-time messages
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws')

    ws.onopen = () => {
      console.log('Debug Panel: WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        // Listen for bus_message type
        if (data.type === 'bus_message' && !isPaused) {
          setMessages(prev => {
            const newMessages = [...prev, data.data]
            // Keep only last 100 messages
            if (newMessages.length > 100) {
              return newMessages.slice(-100)
            }
            return newMessages
          })
        }
      } catch (error) {
        console.error('Debug Panel: Error parsing WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('Debug Panel: WebSocket error:', error)
    }

    wsRef.current = ws

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [isPaused])

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && !isPaused) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, autoScroll, isPaused])

  const fetchMessageHistory = async () => {
    try {
      const response = await fetch(`${API_URL}/api/debug/messages`)
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages || [])
      }
    } catch (error) {
      console.error('Failed to fetch message history:', error)
    }
  }

  // Get unique channels for filter dropdown
  const channels = ['all', ...new Set(messages.map(m => m.channel).filter(Boolean))]

  // Filter messages
  const filteredMessages = messages.filter(m => {
    if (filter !== 'all' && m.channel !== filter) return false
    if (search && !JSON.stringify(m).toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const handleClearMessages = () => {
    setMessages([])
  }

  const handleExport = () => {
    const dataStr = JSON.stringify(filteredMessages, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `debug-messages-${new Date().toISOString()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="debug-panel">
      {/* Controls */}
      <div className="debug-controls">
        <div className="control-group">
          <label htmlFor="channel-filter">Channel:</label>
          <select
            id="channel-filter"
            className="control-select"
            value={filter}
            onChange={e => setFilter(e.target.value)}
          >
            {channels.map(ch => (
              <option key={ch} value={ch}>
                {ch === 'all' ? 'All Channels' : ch}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="search-input">Search:</label>
          <input
            id="search-input"
            type="text"
            className="control-input"
            placeholder="Filter messages..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        <div className="control-buttons">
          <button
            className={`control-button ${isPaused ? 'active' : ''}`}
            onClick={() => setIsPaused(!isPaused)}
            title={isPaused ? 'Resume updates' : 'Pause updates'}
          >
            {isPaused ? '▶️' : '⏸️'}
          </button>

          <label className="control-checkbox">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={e => setAutoScroll(e.target.checked)}
            />
            <span>Auto-scroll</span>
          </label>

          <button
            className="control-button"
            onClick={handleClearMessages}
            title="Clear all messages"
          >
            🗑️ Clear
          </button>

          <button
            className="control-button"
            onClick={handleExport}
            title="Export messages as JSON"
          >
            💾 Export
          </button>
        </div>
      </div>

      {/* Message Stats */}
      <div className="debug-stats">
        <div className="stat">
          <span className="stat-label">Total:</span>
          <span className="stat-value">{messages.length}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Filtered:</span>
          <span className="stat-value">{filteredMessages.length}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Channels:</span>
          <span className="stat-value">{channels.length - 1}</span>
        </div>
        {isPaused && (
          <div className="stat paused">
            <span className="stat-value">⏸️ PAUSED</span>
          </div>
        )}
      </div>

      {/* Messages List */}
      <div className="messages-list">
        {filteredMessages.length === 0 ? (
          <div className="empty-state">
            {messages.length === 0 ? (
              <>
                <div className="empty-icon">📡</div>
                <p>No messages yet</p>
                <span className="empty-hint">Message bus traffic will appear here in real-time</span>
              </>
            ) : (
              <>
                <div className="empty-icon">🔍</div>
                <p>No messages match your filters</p>
                <span className="empty-hint">Try adjusting your channel or search filter</span>
              </>
            )}
          </div>
        ) : (
          <>
            {filteredMessages.map((msg, index) => (
              <MessageCard key={index} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
    </div>
  )
}

export default DebugPanel
