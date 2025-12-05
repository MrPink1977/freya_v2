function CoverageVisualization({ coverage }) {
  if (!coverage) return null

  const { overall, modules, note } = coverage

  const getCoverageColor = (percentage) => {
    if (percentage >= 80) return 'var(--success)'
    if (percentage >= 60) return 'var(--warning)'
    return 'var(--error)'
  }

  const getCoverageLevel = (percentage) => {
    if (percentage >= 80) return 'excellent'
    if (percentage >= 60) return 'good'
    return 'poor'
  }

  return (
    <section className="test-section">
      <div className="section-header">
        <h3>📈 Code Coverage</h3>
        {note && (
          <span className="placeholder-note">{note}</span>
        )}
      </div>

      {/* Overall Coverage */}
      <div className="coverage-overall">
        <div className="coverage-circle">
          <svg width="120" height="120" viewBox="0 0 120 120">
            <circle
              cx="60"
              cy="60"
              r="50"
              fill="none"
              stroke="var(--bg-tertiary)"
              strokeWidth="10"
            />
            <circle
              cx="60"
              cy="60"
              r="50"
              fill="none"
              stroke={getCoverageColor(overall)}
              strokeWidth="10"
              strokeDasharray={`${(overall / 100) * 314} 314`}
              strokeLinecap="round"
              transform="rotate(-90 60 60)"
              style={{ transition: 'stroke-dasharray 0.5s ease' }}
            />
            <text
              x="60"
              y="65"
              textAnchor="middle"
              fontSize="24"
              fontWeight="bold"
              fill="var(--text-primary)"
            >
              {overall.toFixed(1)}%
            </text>
          </svg>
        </div>
        <div className="coverage-info">
          <h4>Overall Coverage</h4>
          <p className={`coverage-level ${getCoverageLevel(overall)}`}>
            {overall >= 80 ? 'Excellent' : overall >= 60 ? 'Good' : 'Needs Improvement'}
          </p>
          <p className="coverage-description">
            {overall >= 80
              ? 'Great job! Your codebase has strong test coverage.'
              : overall >= 60
              ? 'Good start. Consider adding more tests to critical paths.'
              : 'Low coverage. More tests recommended for stability.'}
          </p>
        </div>
      </div>

      {/* Module Coverage */}
      <div className="coverage-modules">
        <h4>Coverage by Module</h4>
        <div className="module-list">
          {modules && modules.length > 0 ? (
            modules.map((module, index) => (
              <div key={index} className="module-item">
                <div className="module-header">
                  <span className="module-name">{module.name}</span>
                  <span
                    className="module-percentage"
                    style={{ color: getCoverageColor(module.coverage) }}
                  >
                    {module.coverage.toFixed(2)}%
                  </span>
                </div>
                <div className="module-bar">
                  <div
                    className="module-fill"
                    style={{
                      width: `${module.coverage}%`,
                      backgroundColor: getCoverageColor(module.coverage)
                    }}
                  />
                </div>
              </div>
            ))
          ) : (
            <p className="empty-state">No module coverage data available</p>
          )}
        </div>
      </div>

      {/* Coverage Stats */}
      <div className="coverage-stats">
        <div className="stat-item">
          <div className="stat-icon">📁</div>
          <div className="stat-content">
            <div className="stat-value">{modules?.length || 0}</div>
            <div className="stat-label">Modules Tested</div>
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-icon">
            {overall >= 80 ? '🎯' : overall >= 60 ? '📊' : '⚠️'}
          </div>
          <div className="stat-content">
            <div className="stat-value">{overall.toFixed(1)}%</div>
            <div className="stat-label">Code Coverage</div>
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-icon">
            {overall >= 80 ? '✓' : overall >= 60 ? '~' : '✗'}
          </div>
          <div className="stat-content">
            <div className="stat-value">
              {overall >= 80 ? 'Good' : overall >= 60 ? 'Fair' : 'Low'}
            </div>
            <div className="stat-label">Quality Rating</div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default CoverageVisualization
