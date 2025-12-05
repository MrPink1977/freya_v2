import { useState, useEffect } from 'react'
import '../styles/ServiceMetrics.css'

function ServiceMetrics({ services }) {
  const [serviceStats, setServiceStats] = useState({})

  // Calculate uptime and enhanced stats for each service
  useEffect(() => {
    const stats = {}
    services.forEach(service => {
      const startTime = service.start_time ? new Date(service.start_time) : null
      const uptime = startTime ? Math.floor((Date.now() - startTime.getTime()) / 1000) : 0

      stats[service.name] = {
        uptime,
        errorCount: service.error_count || 0,
        lastUpdate: service.timestamp || service.last_status_time,
      }
    })
    setServiceStats(stats)
  }, [services])

  const formatUptime = (seconds) => {
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
    return `${Math.floor(seconds / 86400)}d ${Math.floor((seconds % 86400) / 3600)}h`
  }

  const getHealthStatus = (service) => {
    if (!service.healthy) return 'critical'
    const errorCount = service.error_count || 0
    if (errorCount > 5) return 'warning'
    return 'healthy'
  }

  const getHealthColor = (status) => {
    switch (status) {
      case 'healthy': return '#22c55e'
      case 'warning': return '#f59e0b'
      case 'critical': return '#ef4444'
      default: return '#94a3b8'
    }
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    const date = new Date(timestamp)
    const now = new Date()
    const diff = Math.floor((now - date) / 1000)

    if (diff < 60) return 'Just now'
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return date.toLocaleTimeString()
  }

  if (services.length === 0) {
    return (
      <div className="service-metrics-empty">
        <div className="empty-icon">📡</div>
        <p>No services detected</p>
        <span className="empty-hint">Waiting for service status updates...</span>
      </div>
    )
  }

  return (
    <div className="service-metrics">
      {services.map(service => {
        const stats = serviceStats[service.name] || { uptime: 0, errorCount: 0 }
        const healthStatus = getHealthStatus(service)
        const healthColor = getHealthColor(healthStatus)

        return (
          <div key={service.name} className="service-card">
            {/* Header */}
            <div className="service-card-header">
              <div className="service-title">
                <div
                  className="health-indicator"
                  style={{ backgroundColor: healthColor }}
                  title={`Status: ${healthStatus}`}
                />
                <h3>{service.name}</h3>
              </div>
              <div className={`service-badge ${service.status?.toLowerCase() || 'unknown'}`}>
                {service.status || 'Unknown'}
              </div>
            </div>

            {/* Main Stats */}
            <div className="service-stats">
              <div className="stat-item">
                <span className="stat-label">Uptime</span>
                <span className="stat-value">{formatUptime(stats.uptime)}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Errors</span>
                <span className={`stat-value ${stats.errorCount > 0 ? 'error-count' : ''}`}>
                  {stats.errorCount}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Last Update</span>
                <span className="stat-value small">
                  {formatTimestamp(stats.lastUpdate)}
                </span>
              </div>
            </div>

            {/* Placeholder Metrics */}
            <div className="service-metrics-placeholder">
              <div className="metric-placeholder">
                <span className="metric-label">Memory</span>
                <span className="metric-value placeholder">N/A</span>
              </div>
              <div className="metric-placeholder">
                <span className="metric-label">Requests</span>
                <span className="metric-value placeholder">0/sec</span>
              </div>
            </div>

            {/* Health Detail */}
            {service.status_message && (
              <div className="service-detail">
                <span className="detail-icon">ℹ️</span>
                <span className="detail-text">{service.status_message}</span>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default ServiceMetrics
