import React, { useMemo } from 'react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'

// Custom tooltip
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--bg-panel)',
      border: '1px solid var(--border-glow)',
      borderRadius: 4,
      padding: '8px 14px',
      fontFamily: 'var(--font-mono)',
      fontSize: 12,
    }}>
      <p style={{ color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color, margin: '2px 0' }}>
          {p.name}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  )
}

export default function LiveChart({ data }) {
  // data: array of { time, attacks, benign }
  const displayData = useMemo(() => data.slice(-60), [data])

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
          Live Traffic Stream
        </h3>
        <span style={{
          marginLeft: 'auto',
          fontFamily: 'var(--font-mono)',
          fontSize: 10,
          color: 'var(--text-muted)',
        }}>
          Last {displayData.length} ticks
        </span>
      </div>

      <div style={{ height: 220 }}>
        {displayData.length === 0 ? (
          <div className="h-full flex items-center justify-center" style={{
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)',
            fontSize: 12,
          }}>
            Awaiting data stream...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={displayData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gradAttack" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ff1744" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ff1744" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradBenign" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00e676" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#00e676" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(30,58,95,0.5)"
                vertical={false}
              />
              <XAxis
                dataKey="time"
                tick={{ fill: '#4a7fa5', fontSize: 10, fontFamily: 'var(--font-mono)' }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fill: '#4a7fa5', fontSize: 10, fontFamily: 'var(--font-mono)' }}
                axisLine={false}
                tickLine={false}
                allowDecimals={false}
                width={30}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#4a7fa5' }}
              />
              <Area
                type="monotone"
                dataKey="attacks"
                name="Attacks"
                stroke="#ff1744"
                strokeWidth={2}
                fill="url(#gradAttack)"
                dot={false}
                activeDot={{ r: 4, fill: '#ff1744', stroke: '#ff1744' }}
              />
              <Area
                type="monotone"
                dataKey="benign"
                name="Benign"
                stroke="#00e676"
                strokeWidth={2}
                fill="url(#gradBenign)"
                dot={false}
                activeDot={{ r: 4, fill: '#00e676', stroke: '#00e676' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
