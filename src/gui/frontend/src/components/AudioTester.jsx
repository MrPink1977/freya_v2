import { useState, useEffect } from 'react'
import VolumeMeter from './VolumeMeter'
import '../styles/AudioTester.css'

const API_URL = 'http://localhost:8000'

function AudioTester() {
  const [devices, setDevices] = useState(null)
  const [selectedInput, setSelectedInput] = useState(null)
  const [selectedOutput, setSelectedOutput] = useState(null)
  const [recording, setRecording] = useState(false)
  const [volume, setVolume] = useState(0)
  const [ttsText, setTtsText] = useState('')
  const [ttsLoading, setTtsLoading] = useState(false)
  const [ttsResult, setTtsResult] = useState(null)
  const [loading, setLoading] = useState(true)

  // Fetch audio devices on mount
  useEffect(() => {
    fetchDevices()
  }, [])

  // Simulate volume meter when recording
  useEffect(() => {
    if (recording) {
      const interval = setInterval(() => {
        // Random volume between 0-100 for visual demo
        const randomVolume = Math.random() * 100
        setVolume(randomVolume)
      }, 100)
      return () => clearInterval(interval)
    } else {
      setVolume(0)
    }
  }, [recording])

  const fetchDevices = async () => {
    try {
      const response = await fetch(`${API_URL}/api/audio/devices`)
      if (response.ok) {
        const data = await response.json()
        setDevices(data)

        // Auto-select default devices
        const defaultInput = data.input_devices?.find(d => d.is_default)
        const defaultOutput = data.output_devices?.find(d => d.is_default)

        if (defaultInput) setSelectedInput(defaultInput.index)
        if (defaultOutput) setSelectedOutput(defaultOutput.index)
      }
    } catch (error) {
      console.error('Failed to fetch audio devices:', error)
      setDevices({ error: 'Failed to connect to audio service' })
    } finally {
      setLoading(false)
    }
  }

  const handleRecordToggle = () => {
    setRecording(!recording)
  }

  const handleTestTTS = async () => {
    if (!ttsText.trim()) return

    setTtsLoading(true)
    setTtsResult(null)

    try {
      const response = await fetch(`${API_URL}/api/audio/test-tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: ttsText })
      })

      const data = await response.json()
      setTtsResult(data)
    } catch (error) {
      console.error('TTS test failed:', error)
      setTtsResult({ success: false, message: 'Failed to connect to TTS service' })
    } finally {
      setTtsLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="audio-tester-loading">
        <div className="spinner"></div>
        <p>Loading audio devices...</p>
      </div>
    )
  }

  return (
    <div className="audio-tester">
      {/* Device Selection Section */}
      <section className="audio-section">
        <div className="section-header">
          <h3>🎧 Audio Devices</h3>
          {devices?.note && (
            <span className="placeholder-note">{devices.note}</span>
          )}
        </div>

        {devices?.error ? (
          <div className="error-message">
            <span>⚠️ {devices.error}</span>
          </div>
        ) : (
          <div className="device-grid">
            {/* Input Devices */}
            <div className="device-selector">
              <label htmlFor="input-device">Input Device (Microphone)</label>
              <select
                id="input-device"
                className="device-select"
                value={selectedInput || ''}
                onChange={(e) => setSelectedInput(parseInt(e.target.value))}
              >
                {devices?.input_devices?.map(device => (
                  <option key={device.index} value={device.index}>
                    {device.name} {device.is_default ? '(Default)' : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Output Devices */}
            <div className="device-selector">
              <label htmlFor="output-device">Output Device (Speaker)</label>
              <select
                id="output-device"
                className="device-select"
                value={selectedOutput || ''}
                onChange={(e) => setSelectedOutput(parseInt(e.target.value))}
              >
                {devices?.output_devices?.map(device => (
                  <option key={device.index} value={device.index}>
                    {device.name} {device.is_default ? '(Default)' : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </section>

      {/* Microphone Test Section */}
      <section className="audio-section">
        <div className="section-header">
          <h3>🎤 Microphone Test</h3>
          {recording && (
            <span className="placeholder-note">Visual demo only - not recording audio</span>
          )}
        </div>

        <div className="recorder-controls">
          <button
            className={`record-button ${recording ? 'recording' : ''}`}
            onClick={handleRecordToggle}
          >
            {recording ? (
              <>
                <span className="record-icon">⏹</span>
                Stop Recording
              </>
            ) : (
              <>
                <span className="record-icon">⏺</span>
                Start Recording
              </>
            )}
          </button>

          <VolumeMeter level={volume} active={recording} />
        </div>

        {recording && (
          <div className="recording-indicator">
            <span className="pulse-dot"></span>
            <span>Recording in progress...</span>
          </div>
        )}
      </section>

      {/* TTS Test Section */}
      <section className="audio-section">
        <div className="section-header">
          <h3>🔊 Text-to-Speech Test</h3>
          <span className="placeholder-note">Feature coming soon!</span>
        </div>

        <div className="tts-controls">
          <textarea
            className="tts-input"
            placeholder="Type something to convert to speech..."
            value={ttsText}
            onChange={(e) => setTtsText(e.target.value)}
            rows={3}
          />

          <button
            className="tts-button"
            onClick={handleTestTTS}
            disabled={!ttsText.trim() || ttsLoading}
          >
            {ttsLoading ? (
              <>
                <span className="spinner-small"></span>
                Generating...
              </>
            ) : (
              <>
                <span>🎵</span>
                Generate Speech
              </>
            )}
          </button>

          {ttsResult && (
            <div className={`tts-result ${ttsResult.success ? 'success' : 'info'}`}>
              <span>{ttsResult.success ? '✓' : 'ℹ️'}</span>
              <span>{ttsResult.message}</span>
            </div>
          )}
        </div>
      </section>

      {/* Info Box */}
      <div className="info-box">
        <h4>📋 About Audio Testing</h4>
        <ul>
          <li>Device selection shows available audio hardware</li>
          <li>Microphone test provides visual feedback (placeholder)</li>
          <li>TTS testing will be available when Audio Manager is wired</li>
          <li>All features marked as placeholders are UI-only demonstrations</li>
        </ul>
      </div>
    </div>
  )
}

export default AudioTester
