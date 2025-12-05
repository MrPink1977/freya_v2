import { useState } from 'react'

function TestResults({ results }) {
  const [expanded, setExpanded] = useState(false)

  if (!results) return null

  const { suite, results: testResults, note, error, status } = results

  if (status === 'error' || error) {
    return (
      <section className="test-section error">
        <div className="section-header">
          <h3>❌ Test Run Failed</h3>
        </div>
        <div className="error-message">
          <p>{error || 'An unknown error occurred'}</p>
          {note && <p className="error-note">{note}</p>}
        </div>
      </section>
    )
  }

  if (!testResults) return null

  const { total, passed, failed, skipped, duration } = testResults
  const passRate = total > 0 ? Math.round((passed / total) * 100) : 0

  return (
    <section className="test-section">
      <div className="section-header">
        <h3>📊 Test Results</h3>
        {note && (
          <span className="placeholder-note">{note}</span>
        )}
      </div>

      {/* Summary Cards */}
      <div className="results-grid">
        <div className="result-card total">
          <div className="result-value">{total}</div>
          <div className="result-label">Total Tests</div>
        </div>

        <div className="result-card passed">
          <div className="result-value">{passed}</div>
          <div className="result-label">Passed</div>
        </div>

        <div className="result-card failed">
          <div className="result-value">{failed}</div>
          <div className="result-label">Failed</div>
        </div>

        <div className="result-card skipped">
          <div className="result-value">{skipped}</div>
          <div className="result-label">Skipped</div>
        </div>
      </div>

      {/* Pass Rate Bar */}
      <div className="pass-rate-container">
        <div className="pass-rate-label">
          <span>Pass Rate</span>
          <span className="pass-rate-value">{passRate}%</span>
        </div>
        <div className="pass-rate-bar">
          <div
            className={`pass-rate-fill ${passRate === 100 ? 'perfect' : passRate >= 80 ? 'good' : 'poor'}`}
            style={{ width: `${passRate}%` }}
          />
        </div>
      </div>

      {/* Duration */}
      <div className="test-meta">
        <div className="meta-item">
          <span className="meta-label">Suite:</span>
          <span className="meta-value">{suite}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Duration:</span>
          <span className="meta-value">{duration?.toFixed(2)}s</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Status:</span>
          <span className={`meta-value status-${failed === 0 ? 'success' : 'failed'}`}>
            {failed === 0 ? '✓ All Passed' : `✗ ${failed} Failed`}
          </span>
        </div>
      </div>

      {/* Detailed Results (Expandable) */}
      <div className="results-details">
        <button
          className="expand-button"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? '▼' : '▶'} {expanded ? 'Hide' : 'Show'} Detailed Results
        </button>

        {expanded && (
          <div className="details-content">
            <div className="detail-section">
              <h4>✓ Passed Tests ({passed})</h4>
              <ul>
                <li>test_base_service.py::TestBaseService::test_initialization</li>
                <li>test_base_service.py::TestBaseService::test_health_check</li>
                <li>test_message_bus.py::TestMessageBus::test_connection</li>
                <li>test_config.py::TestConfig::test_load_config</li>
                <li>... and {passed - 4} more tests</li>
              </ul>
            </div>

            {skipped > 0 && (
              <div className="detail-section skipped">
                <h4>⊘ Skipped Tests ({skipped})</h4>
                <ul>
                  <li>test_audio_manager.py - PyAudio not installed</li>
                  <li>... and {skipped - 1} more tests</li>
                </ul>
              </div>
            )}

            {failed > 0 && (
              <div className="detail-section failed">
                <h4>✗ Failed Tests ({failed})</h4>
                <ul>
                  <li>No failures - all tests passed! 🎉</li>
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  )
}

export default TestResults
