import { useState, useEffect } from 'react'
import TestResults from './TestResults'
import CoverageVisualization from './CoverageVisualization'
import '../styles/TestRunner.css'

const API_URL = 'http://localhost:8000'

function TestRunner() {
  const [suite, setSuite] = useState('all')
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState(null)
  const [coverage, setCoverage] = useState(null)
  const [progress, setProgress] = useState(0)

  // Fetch coverage data on mount
  useEffect(() => {
    fetchCoverage()
  }, [])

  const fetchCoverage = async () => {
    try {
      const response = await fetch(`${API_URL}/api/tests/coverage`)
      if (response.ok) {
        const data = await response.json()
        setCoverage(data)
      }
    } catch (error) {
      console.error('Failed to fetch coverage:', error)
    }
  }

  const runTests = async () => {
    setRunning(true)
    setProgress(0)
    setResults(null)

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return 90
        }
        return prev + 10
      })
    }, 200)

    try {
      const response = await fetch(`${API_URL}/api/tests/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ suite })
      })

      if (response.ok) {
        const data = await response.json()
        setResults(data)
        setProgress(100)
      }
    } catch (error) {
      console.error('Test run failed:', error)
      setResults({
        status: 'error',
        suite,
        error: 'Failed to connect to test service',
        note: 'Could not reach backend API'
      })
      setProgress(100)
    } finally {
      clearInterval(progressInterval)
      setTimeout(() => {
        setRunning(false)
      }, 500)
    }
  }

  return (
    <div className="test-runner">
      {/* Controls Section */}
      <section className="test-section">
        <div className="section-header">
          <h3>🧪 Test Suite Runner</h3>
          <span className="placeholder-note">Mock results - Real execution coming soon</span>
        </div>

        <div className="test-controls">
          <div className="control-group">
            <label htmlFor="test-suite">Test Suite:</label>
            <select
              id="test-suite"
              className="test-select"
              value={suite}
              onChange={(e) => setSuite(e.target.value)}
              disabled={running}
            >
              <option value="all">All Tests</option>
              <option value="unit">Unit Tests Only</option>
              <option value="integration">Integration Tests Only</option>
            </select>
          </div>

          <button
            className="run-button"
            onClick={runTests}
            disabled={running}
          >
            {running ? (
              <>
                <span className="spinner-small"></span>
                Running Tests...
              </>
            ) : (
              <>
                <span>▶️</span>
                Run Tests
              </>
            )}
          </button>
        </div>

        {/* Progress Bar */}
        {running && (
          <div className="progress-container">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="progress-text">
              {progress}% - Running {suite} tests...
            </div>
          </div>
        )}
      </section>

      {/* Results Section */}
      {results && (
        <TestResults results={results} />
      )}

      {/* Coverage Section */}
      {coverage && (
        <CoverageVisualization coverage={coverage} />
      )}

      {/* Info Box */}
      {!results && !running && (
        <div className="info-box">
          <h4>📋 About Test Runner</h4>
          <ul>
            <li>Select a test suite and click "Run Tests" to see results</li>
            <li>Currently showing mock data to demonstrate UI functionality</li>
            <li>Real pytest execution will be wired when backend is ready</li>
            <li>Coverage data is placeholder - shows Phase 2 stats</li>
          </ul>
        </div>
      )}
    </div>
  )
}

export default TestRunner
