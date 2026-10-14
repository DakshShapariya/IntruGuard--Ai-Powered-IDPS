import React from 'react'

const ATTACK_COLORS = {
  'BENIGN':     { color: '#00e676', bg: 'rgba(0,230,118,0.08)' },
  'DoS':        { color: '#ff1744', bg: 'rgba(255,23,68,0.08)' },
  'DDoS':       { color: '#ff6d00', bg: 'rgba(255,109,0,0.08)' },
  'PortScan':   { color: '#aa00ff', bg: 'rgba(170,0,255,0.08)' },
  'Brute Force':{ color: '#ff9100', bg: 'rgba(255,145,0,0.08)' },
  'Web Attack': { color: '#e040fb', bg: 'rgba(224,64,251,0.08)' },
  'SYN-Flood':  { color: '#f50057', bg: 'rgba(245,0,87,0.08)' },
  'UDP-Flood':  { color: '#ff4081', bg: 'rgba(255,64,129,0.08)' },
}

function getTheme(attack) {
  if (!attack || attack.toUpperCase() === 'BENIGN') return ATTACK_COLORS['BENIGN']
  for (const key of Object.keys(ATTACK_COLORS)) {
    if (attack.toUpperCase().includes(key.toUpperCase())) return ATTACK_COLORS[key]
  }
  return { color: '#ff1744', bg: 'rgba(255,23,68,0.08)' }
}

export default function LogsTable({ logs }) {
  const rows = (logs || []).slice(0, 10)

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
          Recent Activity Log
        </h3>
        <span style={{
          marginLeft: 'auto',
          fontFamily: 'var(--font-mono)',
          fontSize: 10,
          color: 'var(--text-muted)',
        }}>
          Last 10 entries
        </span>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
        }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-glow)' }}>
              {['Timestamp', 'Source IP', 'Destination', 'Attack Type', 'Action'].map((h) => (
                <th key={h} style={{
                  padding: '6px 12px',
                  textAlign: 'left',
                  color: 'var(--text-muted)',
                  fontWeight: 600,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  fontSize: 10,
                  whiteSpace: 'nowrap',
                }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={5} style={{
                  padding: '24px',
                  textAlign: 'center',
                  color: 'var(--text-muted)',
                }}>
                  Monitoring network... no events yet.
                </td>
              </tr>
            ) : rows.map((row, i) => {
              const theme = getTheme(row.attack)
              const isBenign = row.attack?.toUpperCase() === 'BENIGN'
              return (
                <tr
                  key={i}
                  className="slide-in"
                  style={{
                    borderBottom: '1px solid rgba(30,58,95,0.4)',
                    background: i === 0 ? `${theme.bg}` : 'transparent',
                    transition: 'background 0.3s',
                  }}
                >
                  <td style={{ padding: '7px 12px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {row.time}
                  </td>
                  <td style={{ padding: '7px 12px', color: 'var(--accent-cyan)', whiteSpace: 'nowrap' }}>
                    {row.src}
                  </td>
                  <td style={{ padding: '7px 12px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {row.dst}
                  </td>
                  <td style={{ padding: '7px 12px', whiteSpace: 'nowrap' }}>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 5,
                      padding: '2px 8px',
                      borderRadius: 2,
                      background: theme.bg,
                      border: `1px solid ${theme.color}44`,
                      color: theme.color,
                      fontWeight: 700,
                      fontSize: 10,
                      letterSpacing: '0.08em',
                    }}>
                      <span style={{
                        width: 5, height: 5,
                        borderRadius: '50%',
                        background: theme.color,
                        boxShadow: `0 0 4px ${theme.color}`,
                        display: 'inline-block',
                      }} />
                      {row.attack || 'UNKNOWN'}
                    </span>
                  </td>
                  <td style={{ padding: '7px 12px', whiteSpace: 'nowrap' }}>
                    <span style={{
                      color: row.action === 'Blocked' ? '#ffab00' : 'var(--text-muted)',
                      fontWeight: row.action === 'Blocked' ? 700 : 400,
                    }}>
                      {row.action || '—'}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
