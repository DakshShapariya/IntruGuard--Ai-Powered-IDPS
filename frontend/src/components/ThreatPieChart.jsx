import React from 'react'
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts'

const COLORS = {
  'BENIGN':     '#00e676',
  'DoS':        '#ff1744',
  'DDoS':       '#ff6d00',
  'PortScan':   '#aa00ff',
  'Brute Force':'#ff9100',
  'Web Attack': '#e040fb',
  'SYN-Flood':  '#f50057',
  'UDP-Flood':  '#ff4081',
  'Other':      '#546e7a',
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const { name, value } = payload[0]
  return (
    <div style={{
      background: 'var(--bg-panel)',
      border: '1px solid var(--border-glow)',
      borderRadius: 4,
      padding: '8px 14px',
      fontFamily: 'var(--font-mono)',
      fontSize: 12,
    }}>
      <p style={{ color: COLORS[name] || '#fff', margin: 0 }}>
        {name}: <strong>{value}</strong>
      </p>
    </div>
  )
}

const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  if (percent < 0.05) return null
  const RADIAN = Math.PI / 180
  const r = innerRadius + (outerRadius - innerRadius) * 0.5
  const x = cx + r * Math.cos(-midAngle * RADIAN)
  const y = cy + r * Math.sin(-midAngle * RADIAN)
  return (
    <text
      x={x} y={y}
      fill="rgba(255,255,255,0.85)"
      textAnchor="middle"
      dominantBaseline="central"
      style={{ fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 600 }}
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  )
}

export default function ThreatPieChart({ distribution }) {
  // distribution: { 'BENIGN': 12, 'DoS': 4, ... }
  const data = Object.entries(distribution || {})
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)

  return (
    <div className="panel p-5 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-1.5 h-6 rounded-full" style={{ background: 'var(--accent-cyan)' }} />
        <h3 style={{
          fontFamily: 'var(--font-display)',
          color: 'var(--accent-cyan)',
          fontSize: 13,
          letterSpacing: '0.15em',
          textTransform: 'uppercase',
          fontWeight: 700,
          margin: 0,
        }}>
          Threat Distribution
        </h3>
      </div>

      <div style={{ height: 220 }}>
        {data.length === 0 ? (
          <div className="h-full flex items-center justify-center" style={{
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)',
            fontSize: 12,
          }}>
            No data yet...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={85}
                paddingAngle={2}
                dataKey="value"
                labelLine={false}
                label={renderCustomLabel}
              >
                {data.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={COLORS[entry.name] || COLORS['Other']}
                    stroke="var(--bg-card)"
                    strokeWidth={2}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  color: '#4a7fa5',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
