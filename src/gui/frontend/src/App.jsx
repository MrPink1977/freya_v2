import { useState, useEffect, useRef } from 'react'
import ServiceMetrics from './components/ServiceMetrics'
import DebugPanel from './components/DebugPanel'
import AudioTester from './components/AudioTester'
import TestRunner from './components/TestRunner'
import ErrorBoundary from './components/ErrorBoundary'

const API_URL = 'http://localhost:8000'
const WS_URL = 'ws://localhost:8000/ws'

function App() {
  // State
  const [services, setServices] = useState([])
  const [messages, setMessages] = useState([])
  const [tools, setTools] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [wsConnected, setWsConnected] = useState(false)
  const [activeTab, setActiveTab] = useState('home')
  const [theme, setTheme] = useState('dark')

  const wsRef = useRef(null)
  const messagesEndRef = useRef(null)

  // Theme toggle
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  }

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyboard = (e) => {
      // Check if Ctrl/Cmd is pressed
      if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
          case '1':
            e.preventDefault()
            setActiveTab('home')
            break
          case '2':
            e.preventDefault()
            setActiveTab('audio')
            break
          case '3':
            e.preventDefault()
            setActiveTab('debug')
            break
          case '4':
            e.preventDefault()
            setActiveTab('tests')
            break
          case '5':
            e.preventDefault()
            setActiveTab('tools')
            break
          case 'd':
            e.preventDefault()
            setActiveTab('debug')
            break
          case 't':
            e.preventDefault()
            setActiveTab('tests')
            break
        }
      }
    }

    window.addEventListener('keydown', handleKeyboard)
    return () => window.removeEventListener('keydown', handleKeyboard)
  }, [])

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

  // Tab definitions
  const tabs = [
    { id: 'home', label: 'Home', shortcut: 'Ctrl+1' },
    { id: 'audio', label: 'Audio', shortcut: 'Ctrl+2' },
    { id: 'debug', label: 'Debug', shortcut: 'Ctrl+3' },
    { id: 'tests', label: 'Tests', shortcut: 'Ctrl+4' },
    { id: 'tools', label: 'Tools', shortcut: 'Ctrl+5' },
  ]

  // Render tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'home':
        return <HomeTab
          services={services}
          messages={messages}
          inputValue={inputValue}
          setInputValue={setInputValue}
          sendMessage={sendMessage}
          wsConnected={wsConnected}
          messagesEndRef={messagesEndRef}
        />

      case 'audio':
        return <AudioTab />

      case 'debug':
        return <DebugTab />

      case 'tests':
        return <TestsTab />

      case 'tools':
        return <ToolsTab tools={tools} />

      default:
        return <HomeTab
          services={services}
          messages={messages}
          inputValue={inputValue}
          setInputValue={setInputValue}
          sendMessage={sendMessage}
          wsConnected={wsConnected}
          messagesEndRef={messagesEndRef}
        />
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div>
            <h1>Freya v2.0 Dashboard</h1>
            <p>Real-time monitoring and control interface</p>
          </div>
          <button className="theme-toggle" onClick={toggleTheme} title="Toggle theme">
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>

        {/* Tab Navigation */}
        <nav className="tab-nav">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              title={tab.shortcut}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="main-content">
        <ErrorBoundary>
          <div className="tab-content">
            {renderTabContent()}
          </div>
        </ErrorBoundary>
      </main>

      {/* Connection Status Indicator */}
      <div className={`connection-status ${wsConnected ? 'connected' : 'disconnected'}`}>
        <div className={`status-dot ${wsConnected ? 'healthy' : 'unhealthy'}`}></div>
        <span>{wsConnected ? 'Connected' : 'Disconnected'}</span>
      </div>
    </div>
  )
}

// ============================================================================
// Tab Components
// ============================================================================

function HomeTab({ services, messages, inputValue, setInputValue, sendMessage, wsConnected, messagesEndRef }) {
  return (
    <div className="home-tab">
      {/* Left Panel - Services */}
      <div className="panel">
        <h2 className="panel-header">Services Status</h2>
        <ServiceMetrics services={services} />
      </div>

      {/* Right Panel - Chat */}
      <div className="panel">
        <h2 className="panel-header">Conversation</h2>
        <div className="chat-window">
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="empty-state">
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
    </div>
  )
}

function AudioTab() {
  return (
    <div className="audio-tab">
      <AudioTester />
    </div>
  )
}

function DebugTab() {
  return (
    <div className="debug-tab">
      <DebugPanel />
    </div>
  )
}

function TestsTab() {
  return (
    <div className="tests-tab">
      <TestRunner />
    </div>
  )
}

function ToolsTab({ tools }) {
  return (
    <div className="tools-tab">
      <div className="panel">
        <h2 className="panel-header">MCP Tool Calls History</h2>
        <div className="tools-container">
          {tools.length === 0 ? (
            <p className="empty-state">
              No tool calls yet
            </p>
          ) : (
            tools.slice(-20).reverse().map((tool) => (
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
                  <div className="tool-error">
                    {tool.error}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default App
