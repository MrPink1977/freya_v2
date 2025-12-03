import { useState, useEffect, useRef } from 'react'

const API_URL = 'http://localhost:8000'
const WS_URL = 'ws://localhost:8000/ws'

function App() {
  const [services, setServices] = useState([])
  const [messages, setMessages] = useState([])
  const [tools, setTools] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [wsConnected, setWsConnected] = useState(false)
  const wsRef = useRef(null)
  const messagesEndRef = useRef(null)

  // WebSocket connection
  useEffect(() => {
    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        console.log('WebSocket connected')
        setWsConnected(true)
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setWsConnected(false)
        // Attempt reconnection after 3 seconds
        setTimeout(connectWebSocket, 3000)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleWebSocketMessage(data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Error connecting to WebSocket:', error)
      setTimeout(connectWebSocket, 3000)
    }
  }

  const handleWebSocketMessage = (data) => {
    console.log('Received WebSocket message:', data)

    switch (data.type) {
      case 'initial_state':
        setServices(data.data.services || [])
        setMessages(data.data.chat_history || [])
        setTools(data.data.tool_history || [])
        break

      case 'service_status':
        setServices(prev => {
          const newServices = [...prev]
          const index = newServices.findIndex(s => s.name === data.data.name)
          if (index >= 0) {
            newServices[index] = { ...newServices[index], ...data.data }
          } else {
            newServices.push(data.data)
          }
          return newServices
        })
        break

      case 'chat_message':
        setMessages(prev => [...prev, data.data])
        break

      case 'tool_call':
        setTools(prev => {
          const newTools = [...prev]
          const index = newTools.findIndex(t => t.id === data.data.id)
          if (index >= 0) {
            newTools[index] = { ...newTools[index], ...data.data }
          } else {
            newTools.push(data.data)
          }
          return newTools
        })
        break
    }
  }

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (e) => {
    e.preventDefault()

    if (!inputValue.trim()) return

    try {
      const response = await fetch(`${API_URL}/api/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: inputValue }),
      })

      if (response.ok) {
        setInputValue('')
      } else {
        console.error('Error sending message:', await response.text())
      }
    } catch (error) {
      console.error('Error sending message:', error)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Freya v2.0 Dashboard</h1>
        <p>Real-time monitoring and control interface</p>
      </header>

      <main className="main-content">
        {/* Left Panel - Services */}
        <div className="panel">
          <h2 className="panel-header">Services</h2>
          <div className="services-grid">
            {services.length === 0 ? (
              <p style={{ color: '#94a3b8', textAlign: 'center', padding: '2rem' }}>
                No services found. Waiting for data...
              </p>
            ) : (
              services.map((service) => (
                <div key={service.name} className="service-item">
                  <span className="service-name">{service.name}</span>
                  <div className="service-status">
                    <div className={`status-dot ${service.healthy ? 'healthy' : 'unhealthy'}`}></div>
                    <span>{service.status}</span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Tools Log */}
          <h2 className="panel-header" style={{ marginTop: '2rem' }}>Tool Calls</h2>
          <div className="tools-container">
            {tools.length === 0 ? (
              <p style={{ color: '#94a3b8', textAlign: 'center', padding: '1rem' }}>
                No tool calls yet
              </p>
            ) : (
              tools.slice(-10).reverse().map((tool) => (
                <div key={tool.id} className="tool-item">
                  <div className="tool-header">
                    <span className="tool-name">{tool.tool_name}</span>
                    <span className={`tool-status ${tool.success ? 'success' : 'error'}`}>
                      {tool.success ? 'Success' : 'Error'}
                    </span>
                  </div>
                  {tool.duration && (
                    <div className="tool-duration">
                      Duration: {tool.duration.toFixed(2)}s
                    </div>
                  )}
                  {tool.error && (
                    <div style={{ color: '#fca5a5', fontSize: '0.875rem', marginTop: '0.25rem' }}>
                      {tool.error}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Panel - Chat */}
        <div className="panel">
          <h2 className="panel-header">Conversation</h2>
          <div className="chat-window">
            <div className="messages-container">
              {messages.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
                  <p>No messages yet. Start a conversation!</p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div key={msg.id} className={`message ${msg.role}`}>
                    <div>{msg.content}</div>
                    <div className="message-meta">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                      {msg.location && ` • ${msg.location}`}
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-container">
              <form onSubmit={sendMessage} className="chat-input-form">
                <input
                  type="text"
                  className="chat-input"
                  placeholder="Type your message..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  disabled={!wsConnected}
                />
                <button
                  type="submit"
                  className="send-button"
                  disabled={!wsConnected || !inputValue.trim()}
                >
                  Send
                </button>
              </form>
            </div>
          </div>
        </div>
      </main>

      {/* Connection Status Indicator */}
      <div className={`connection-status ${wsConnected ? 'connected' : 'disconnected'}`}>
        <div className={`status-dot ${wsConnected ? 'healthy' : 'unhealthy'}`}></div>
        <span>{wsConnected ? 'Connected' : 'Disconnected'}</span>
      </div>
    </div>
  )
}

export default App
