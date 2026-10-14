import React from 'react'

export default function StatusIndicator({ isAttack, lastEvent, isConnected }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 20,
      padding: '10px 16px',
      background: 'var(--bg-card)',
      border: `1px solid ${isAttack ? 'rgba(255,23,68,0.4)' : 'rgba(0,230,118,0.3)'}`,
      borderRadius: 4,
      transition: 'border-color 0.5s',
    }}>
      {/* Main status dot */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div
          className={isAttack ? 'glow-red' : 'glow-green'}
          style={{
            width: 14,
            height: 14,
            borderRadius: '50%',
            background: isAttack ? 'var(--accent-red)' : 'var(--accent-green)',
            flexShrink: 0,
          }}
        />
        <span style={{
          fontFamily: 'var(--font-display)',
          fontWeight: 700,
          fontSize: 14,
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          color: isAttack ? 'var(--accent-red)' : 'var(--accent-green)',
        }}>
          {isAttack ? 'THREAT DETECTED' : 'NETWORK SAFE'}
        </span>
      </div>

      {/* Separator */}
      <div style={{ width: 1, height: 20, background: 'var(--border-glow)' }} />

      {/* Connection status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <div
          className={isConnected ? 'blink' : ''}
          style={{
            width: 7, height: 7,
            borderRadius: '50%',
            background: isConnected ? '#00e5ff' : '#546e7a',
          }}
        />
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: isConnected ? 'var(--accent-cyan)' : '#546e7a',
          letterSpacing: '0.05em',
        }}>
          {isConnected ? 'LIVE' : 'OFFLINE'}
        </span>
      </div>

      {/* Last event */}
      {lastEvent && (
        <>
          <div style={{ width: 1, height: 20, background: 'var(--border-glow)' }} />
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--text-muted)',
          }}>
            Last: <span style={{ color: 'var(--text-primary)' }}>{lastEvent}</span>
          </span>
        </>
      )}
    </div>
  )
}
