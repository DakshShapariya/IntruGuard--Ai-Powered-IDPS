import React, { useState, useEffect, useRef, useCallback } from 'react'
import { fetchLiveData } from '../services/api'
import StatsCard from '../components/StatsCard'
import LiveChart from '../components/LiveChart'
import ThreatPieChart from '../components/ThreatPieChart'
import LogsTable from '../components/LogsTable'
import StatusIndicator from '../components/StatusIndicator'

const POLL_INTERVAL_MS = 1500

// Maintain rolling chart data in memory (max 120 points)
const MAX_CHART_POINTS = 120

export default function Dashboard() {
  const [stats, setStats] = useState({ total: 0, attacks: 0, benign: 0, blocked: 0 })
  const [logs, setLogs] = useState([])
  const [distribution, setDistribution] = useState({})
  const [chartData, setChartData] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const prevStatsRef = useRef(stats)
  const intervalRef = useRef(null)

  const isAttack = stats.attacks > 0 && logs.length > 0 &&
    logs[0]?.attack?.toUpperCase() !== 'BENIGN'

  const tick = useCallback(async () => {
    try {
      const data = await fetchLiveData()

      setStats(data.stats)
      setLogs(data.logs)
      setDistribution(data.distribution || {})
      setIsConnected(true)
      setError(null)

      const now = new Date()
      const timeLabel = now.toLocaleTimeString('en-GB', {
        hour: '2-digit', minute: '2-digit', second: '2-digit'
      })
      setLastUpdated(timeLabel)

      setChartData(prev => {
        const next = [
          ...prev,
          {
            time: timeLabel,
            attacks: data.stats.attacks,
            benign: data.stats.benign,
          }
        ]
        return next.slice(-MAX_CHART_POINTS)
      })

      prevStatsRef.current = data.stats
    } catch (err) {
      setIsConnected(false)
      setError('Cannot reach backend — is Flask running on port 5000?')
    }
  }, [])

  useEffect(() => {
    tick()
    intervalRef.current = setInterval(tick, POLL_INTERVAL_MS)
    return () => clearInterval(intervalRef.current)
  }, [tick])

  const deltaAttacks = stats.attacks - prevStatsRef.current.attacks
  const deltaBenign  = stats.benign  - prevStatsRef.current.benign

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-void)',
      position: 'relative',
      zIndex: 1,
    }}>
      {/* Header */}
      <header style={{
        background: 'var(--bg-panel)',
        borderBottom: '1px solid var(--border-glow)',
        padding: '14px 28px',
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        {/* Logo mark */}
        <div style={{
          width: 36, height: 36,
          border: '2px solid var(--accent-cyan)',
          borderRadius: 4,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          boxShadow: '0 0 12px rgba(0,229,255,0.3)',
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z"
              stroke="var(--accent-cyan)" strokeWidth="1.5" fill="none"/>
            <path d="M9 12l2 2 4-4" stroke="var(--accent-cyan)" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </div>

        <div>
          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 20,
            fontWeight: 800,
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
            color: 'var(--accent-cyan)',
            margin: 0,
            lineHeight: 1,
          }}>
            IntruGuard
          </h1>
          <p style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--text-muted)',
            margin: 0,
            letterSpacing: '0.12em',
          }}>
            INTRUSION DETECTION SYSTEM
          </p>
        </div>

        {/* Status */}
        <div style={{ marginLeft: 'auto' }}>
          <StatusIndicator
            isAttack={isAttack}
            lastEvent={lastUpdated}
            isConnected={isConnected}
          />
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div style={{
          background: 'rgba(255,23,68,0.08)',
          border: '1px solid rgba(255,23,68,0.3)',
          borderTop: 0,
          padding: '8px 28px',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--accent-red)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <span>⚠</span>
          {error}
        </div>
      )}

      {/* Main content */}
      <main style={{ padding: '20px 28px', position: 'relative', zIndex: 1 }}>
        {/* Stats row */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 16,
          marginBottom: 20,
        }}>
          <StatsCard
            label="Total Flows"
            value={stats.total}
            type="total"
            icon="⚡"
            delta={deltaAttacks + deltaBenign > 0 ? deltaAttacks + deltaBenign : undefined}
          />
          <StatsCard
            label="Attacks Detected"
            value={stats.attacks}
            type="attacks"
            icon="🚨"
            delta={deltaAttacks > 0 ? deltaAttacks : undefined}
          />
          <StatsCard
            label="Benign Traffic"
            value={stats.benign}
            type="benign"
            icon="✓"
            delta={deltaBenign > 0 ? deltaBenign : undefined}
          />
          <StatsCard
            label="IPs Blocked"
            value={stats.blocked}
            type="blocked"
            icon="🛡"
          />
        </div>

        {/* Charts row */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '2fr 1fr',
          gap: 16,
          marginBottom: 20,
        }}>
          <LiveChart data={chartData} />
          <ThreatPieChart distribution={distribution} />
        </div>

        {/* Logs table */}
        <LogsTable logs={logs} />

        {/* Footer */}
        <footer style={{
          marginTop: 20,
          paddingTop: 12,
          borderTop: '1px solid var(--border-glow)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--text-muted)',
          }}>
            INTRUGUARD IDS · POLLING EVERY {POLL_INTERVAL_MS}ms
          </span>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--text-muted)',
          }}>
            {isConnected
              ? `✓ CONNECTED · Flask :5000`
              : '✗ DISCONNECTED'}
          </span>
        </footer>
      </main>
    </div>
  )
}
