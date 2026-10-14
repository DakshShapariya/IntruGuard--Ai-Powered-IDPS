import React, { useEffect, useRef } from 'react'

const THEMES = {
  total:   { accent: '#00e5ff',  label: 'var(--accent-cyan)',  glow: 'glow-cyan'  },
  attacks: { accent: '#ff1744',  label: 'var(--accent-red)',   glow: 'glow-red'   },
  benign:  { accent: '#00e676',  label: 'var(--accent-green)', glow: 'glow-green' },
  blocked: { accent: '#ffab00',  label: '#ffab00',             glow: ''           },
}

export default function StatsCard({ label, value, type = 'total', icon, delta }) {
  const theme = THEMES[type] || THEMES.total
  const prevRef = useRef(value)
  const changed = prevRef.current !== value

  useEffect(() => {
    prevRef.current = value
  }, [value])

  return (
    <div
      className={`panel bracket-corner relative p-5 flex flex-col gap-2 transition-all duration-300 ${theme.glow}`}
      style={{ borderColor: `${theme.accent}33` }}
    >
      {/* Top label row */}
      <div className="flex items-center justify-between">
        <span
          className="text-xs tracking-widest uppercase font-semibold"
          style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
        >
          {label}
        </span>
        <span className="text-lg opacity-70">{icon}</span>
      </div>

      {/* Value */}
      <div
        key={value}
        className="text-5xl font-extrabold tabular-nums leading-none"
        style={{
          color: theme.accent,
          fontFamily: 'var(--font-display)',
          textShadow: `0 0 20px ${theme.accent}66`,
          animation: changed ? 'countUp 0.3s ease-out' : 'none',
        }}
      >
        {value.toLocaleString()}
      </div>

      {/* Delta badge */}
      {delta !== undefined && (
        <div
          className="text-xs"
          style={{ color: delta > 0 ? theme.accent : 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
        >
          {delta > 0 ? `+${delta}` : delta} since last refresh
        </div>
      )}

      {/* Decorative bar */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5" style={{
        background: `linear-gradient(90deg, transparent, ${theme.accent}66, transparent)`
      }} />
    </div>
  )
}
