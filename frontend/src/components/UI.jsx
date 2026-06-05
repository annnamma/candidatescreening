import { Loader2, BrainCircuit } from 'lucide-react'

// ── Logo ──────────────────────────────────────────────────────────────────────
export function Logo({ size = 'md' }) {
  const sizes = { sm: 'text-lg', md: 'text-2xl', lg: 'text-3xl' }
  return (
    <div className={`flex items-center gap-2.5 font-display ${sizes[size]}`}>
      <div className="relative">
        <div className="w-8 h-8 rounded-xl flex items-center justify-center"
          style={{ background: 'linear-gradient(135deg, #3d5aff, #7c8fff)' }}>
          <BrainCircuit size={18} className="text-white" />
        </div>
        <div className="absolute inset-0 rounded-xl blur-md opacity-40"
          style={{ background: 'linear-gradient(135deg, #3d5aff, #7c8fff)' }} />
      </div>
      <span className="gradient-text font-display">ScreenAI</span>
    </div>
  )
}

// ── Spinner ───────────────────────────────────────────────────────────────────
export function Spinner({ size = 20, className = '' }) {
  return <Loader2 size={size} className={`animate-spin ${className}`} style={{ color: '#3d5aff' }} />
}

// ── Full-page loader ──────────────────────────────────────────────────────────
export function PageLoader({ message = 'Loading...' }) {
  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center gap-4 z-50"
      style={{ background: 'var(--bg-primary)' }}>
      <Spinner size={36} />
      <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{message}</p>
    </div>
  )
}

// ── Progress bar ──────────────────────────────────────────────────────────────
export function ProgressBar({ value, max, label }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div className="space-y-1.5">
      {label && (
        <div className="flex items-center justify-between text-xs" style={{ color: 'var(--text-secondary)' }}>
          <span>{label}</span>
          <span>{value} / {max}</span>
        </div>
      )}
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

// ── Score ring ────────────────────────────────────────────────────────────────
export function ScoreRing({ score }) {
  const r = 54
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  const color = score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444'
  const label = score >= 75 ? 'Excellent' : score >= 50 ? 'Good' : 'Needs Work'

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-36 h-36">
        <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
          <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
          <circle
            cx="60" cy="60" r={r}
            fill="none" stroke={color} strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)', filter: `drop-shadow(0 0 8px ${color})` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold font-display" style={{ color }}>{score}</span>
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>/ 100</span>
        </div>
      </div>
      <span className="text-sm font-medium" style={{ color }}>{label}</span>
    </div>
  )
}

// ── Error banner ──────────────────────────────────────────────────────────────
export function ErrorBanner({ message, onDismiss }) {
  if (!message) return null
  return (
    <div className="flex items-start gap-3 p-4 rounded-xl border animate-fade-in"
      style={{ background: 'rgba(239,68,68,0.08)', borderColor: 'rgba(239,68,68,0.2)' }}>
      <span className="text-sm flex-1" style={{ color: '#fca5a5' }}>{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="text-xs opacity-60 hover:opacity-100 transition-opacity"
          style={{ color: '#fca5a5' }}>✕</button>
      )}
    </div>
  )
}

// ── Step indicator ────────────────────────────────────────────────────────────
export function StepIndicator({ steps, current }) {
  return (
    <div className="flex items-center gap-2">
      {steps.map((step, i) => {
        const state = i < current ? 'done' : i === current ? 'active' : 'pending'
        return (
          <div key={i} className="flex items-center gap-2">
            <div className="flex items-center gap-2">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                state === 'done' ? 'text-white' :
                state === 'active' ? 'text-white' : 'text-opacity-40'
              }`} style={{
                background: state === 'done' ? '#22c55e' :
                  state === 'active' ? 'var(--accent)' : 'rgba(255,255,255,0.06)',
                color: state === 'pending' ? 'var(--text-muted)' : 'white',
                boxShadow: state === 'active' ? '0 0 12px var(--accent-glow)' : 'none',
              }}>
                {state === 'done' ? '✓' : i + 1}
              </div>
              <span className="text-xs font-medium hidden sm:block" style={{
                color: state === 'active' ? 'var(--text-primary)' : 'var(--text-muted)'
              }}>{step}</span>
            </div>
            {i < steps.length - 1 && (
              <div className="w-8 h-px mx-1" style={{
                background: i < current ? '#22c55e' : 'rgba(255,255,255,0.08)'
              }} />
            )}
          </div>
        )
      })}
    </div>
  )
}