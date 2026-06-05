import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  CheckCircle2, XCircle, ArrowRight, Download,
  RotateCcw, TrendingUp, AlertTriangle, Star,
  Bookmark, Trophy, ExternalLink
} from 'lucide-react'
import { getSummary, downloadReport } from '../services/api'
import { Logo, Spinner, ScoreRing, ErrorBanner } from '../components/UI'

export default function SummaryPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { sessionId, role, candidateData } = location.state || {}

  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!sessionId) { navigate('/'); return }
    fetchSummary()
  }, [sessionId])

  const fetchSummary = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getSummary(sessionId)
      setSummary(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (!sessionId) return null

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Bg orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] rounded-full opacity-8 blur-[120px]"
          style={{ background: 'radial-gradient(ellipse, #3d5aff, transparent)' }} />
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-8 py-5 border-b"
        style={{ borderColor: 'var(--border)' }}>
        <Logo />
        <div className="flex items-center gap-3">
          {summary && (
            <button
              className="btn-ghost text-sm"
              onClick={() => downloadReport(sessionId)}
            >
              <Download size={15} /> Download Report
            </button>
          )}
          <button
            className="btn-ghost text-sm"
            onClick={() => navigate('/')}
          >
            <RotateCcw size={15} /> New Interview
          </button>
        </div>
      </header>

      <main className="relative z-10 max-w-4xl mx-auto px-4 py-12 space-y-8">

        {loading ? (
          <div className="flex flex-col items-center gap-5 py-24">
            <Spinner size={40} />
            <div className="text-center space-y-1">
              <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                Generating Your Evaluation…
              </p>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                Our AI is analysing your answers. This may take a moment.
              </p>
            </div>
          </div>
        ) : error ? (
          <div className="py-12">
            <ErrorBanner message={error} />
            <button className="btn-primary mt-4" onClick={fetchSummary}>Retry</button>
          </div>
        ) : summary ? (
          <>
            {/* Hero */}
            <div className="card p-8 text-center space-y-6 animate-fade-up">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium mb-2"
                  style={{ background: 'rgba(61,90,255,0.1)', color: '#93acff', border: '1px solid rgba(61,90,255,0.2)' }}>
                  <Trophy size={14} /> Interview Complete
                </div>
                <h1 className="text-4xl font-display gradient-text">
                  {summary.candidate_name ? `${summary.candidate_name}'s Results` : 'Interview Results'}
                </h1>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Role: <span style={{ color: 'var(--text-primary)' }}>{summary.role}</span>
                  {' '}• Session #{summary.session_id}
                </p>
              </div>

              {summary.score !== null && summary.score !== undefined && (
                <div className="flex justify-center py-4">
                  <ScoreRing score={summary.score} />
                </div>
              )}
            </div>

            {/* Overall assessment */}
            <div className="card p-6 space-y-3 animate-fade-up animate-delay-100">
              <div className="flex items-center gap-2">
                <Star size={18} style={{ color: '#f59e0b' }} />
                <h2 className="font-semibold text-base" style={{ color: 'var(--text-primary)' }}>
                  Overall Assessment
                </h2>
              </div>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)', lineHeight: '1.75' }}>
                {summary.overall_assessment}
              </p>
            </div>

            {/* Strengths + Weaknesses */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Strengths */}
              <div className="card p-6 space-y-4 animate-fade-up animate-delay-200">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                    style={{ background: 'rgba(34,197,94,0.1)' }}>
                    <TrendingUp size={16} style={{ color: '#22c55e' }} />
                  </div>
                  <h2 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Strengths</h2>
                </div>
                <ul className="space-y-3">
                  {summary.strengths.map((s, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <CheckCircle2 size={15} className="mt-0.5 shrink-0" style={{ color: '#22c55e' }} />
                      <span className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{s}</span>
                    </li>
                  ))}
                  {summary.strengths.length === 0 && (
                    <li className="text-sm" style={{ color: 'var(--text-muted)' }}>No strengths noted.</li>
                  )}
                </ul>
              </div>

              {/* Weaknesses */}
              <div className="card p-6 space-y-4 animate-fade-up animate-delay-300">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                    style={{ background: 'rgba(239,68,68,0.08)' }}>
                    <AlertTriangle size={16} style={{ color: '#ef4444' }} />
                  </div>
                  <h2 className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                    Areas for Improvement
                  </h2>
                </div>
                <ul className="space-y-3">
                  {summary.weaknesses.map((w, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <XCircle size={15} className="mt-0.5 shrink-0" style={{ color: '#f87171' }} />
                      <span className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{w}</span>
                    </li>
                  ))}
                  {summary.weaknesses.length === 0 && (
                    <li className="text-sm" style={{ color: 'var(--text-muted)' }}>No significant weaknesses noted.</li>
                  )}
                </ul>
              </div>
            </div>

            {/* Recommendations */}
            <div className="card p-6 space-y-4 animate-fade-up animate-delay-400">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: 'rgba(61,90,255,0.1)' }}>
                  <Bookmark size={16} style={{ color: 'var(--accent)' }} />
                </div>
                <h2 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Recommendations</h2>
              </div>
              <ul className="space-y-3">
                {summary.recommendations.map((r, i) => (
                  <li key={i} className="flex items-start gap-3 p-3 rounded-xl"
                    style={{ background: 'rgba(61,90,255,0.05)', border: '1px solid rgba(61,90,255,0.1)' }}>
                    <div className="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold"
                      style={{ background: 'rgba(61,90,255,0.2)', color: '#93acff' }}>
                      {i + 1}
                    </div>
                    <span className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{r}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 animate-fade-up animate-delay-500">
              <button
                className="btn-primary flex-1 py-3.5"
                onClick={() => downloadReport(sessionId)}
              >
                <Download size={17} /> Download PDF Report
              </button>
              <button
                className="btn-ghost flex-1 py-3.5"
                onClick={() => navigate('/')}
              >
                <RotateCcw size={17} /> Start New Interview
              </button>
            </div>
          </>
        ) : null}
      </main>
    </div>
  )
}