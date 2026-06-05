import { useState, useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  Send, ChevronRight, MessageSquare, Lightbulb,
  Clock, Zap, AlertCircle
} from 'lucide-react'
import { getQuestion, submitAnswer } from '../services/api'
import { Logo, Spinner, ProgressBar, ErrorBanner } from '../components/UI'

export default function InterviewPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const textareaRef = useRef(null)

  const { sessionId, role, totalQuestions, candidateData } = location.state || {}

  const [question, setQuestion] = useState(null)
  const [answer, setAnswer] = useState('')
  const [questionNumber, setQuestionNumber] = useState(1)
  const [total, setTotal] = useState(totalQuestions || 5)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [isAdaptive, setIsAdaptive] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [nextAvailable, setNextAvailable] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [timerActive, setTimerActive] = useState(false)

  // Timer
  useEffect(() => {
    if (!timerActive) return
    const interval = setInterval(() => setElapsed(e => e + 1), 1000)
    return () => clearInterval(interval)
  }, [timerActive])

  const formatTime = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`

  // Redirect if no session
  useEffect(() => {
    if (!sessionId) {
      navigate('/')
    }
  }, [sessionId, navigate])

  // Fetch first question
  useEffect(() => {
    if (sessionId) fetchQuestion()
  }, [sessionId])

  const fetchQuestion = async () => {
    setLoading(true)
    setError('')
    setAnswer('')
    setSubmitted(false)
    setElapsed(0)
    try {
      const data = await getQuestion(sessionId)
      setQuestion(data)
      setQuestionNumber(data.question_number)
      setTotal(data.total_questions)
      setIsAdaptive(data.question_type === 'adaptive')
      setTimerActive(true)
    } catch (err) {
      if (err.message.includes('No more questions')) {
        navigate('/summary', { state: { sessionId, role, candidateData } })
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!answer.trim()) return setError('Please write an answer before submitting.')
    if (answer.trim().length < 10) return setError('Please provide a more detailed answer.')

    setSubmitting(true)
    setError('')
    setTimerActive(false)
    try {
      const data = await submitAnswer(sessionId, question.question_id, answer)
      setSubmitted(true)
      setNextAvailable(data.next_question_available)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleNext = async () => {
    if (!nextAvailable) {
      navigate('/summary', { state: { sessionId, role, candidateData } })
    } else {
      await fetchQuestion()
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && !submitted) {
      handleSubmit()
    }
  }

  if (!sessionId) return null

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-primary)' }}>
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 rounded-full opacity-8 blur-[100px]"
          style={{ background: 'radial-gradient(circle, #3d5aff, transparent)' }} />
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-8 py-4 border-b"
        style={{ borderColor: 'var(--border)', background: 'rgba(9,12,17,0.8)', backdropFilter: 'blur(12px)' }}>
        <Logo size="sm" />

        <div className="flex items-center gap-3">
          {isAdaptive && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
              style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)' }}>
              <Zap size={13} style={{ color: '#f59e0b' }} />
              <span className="text-xs font-medium" style={{ color: '#f59e0b' }}>Adaptive</span>
            </div>
          )}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)' }}>
            <Clock size={13} style={{ color: 'var(--text-secondary)' }} />
            <span className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>
              {formatTime(elapsed)}
            </span>
          </div>
          <div className="px-3 py-1.5 rounded-lg text-xs"
            style={{ background: 'rgba(61,90,255,0.1)', color: '#93acff', border: '1px solid rgba(61,90,255,0.2)' }}>
            {role}
          </div>
        </div>
      </header>

      {/* Progress */}
      <div className="relative z-10 px-8 pt-4">
        <ProgressBar value={questionNumber - (submitted ? 0 : 1)} max={total}
          label={`Question ${questionNumber} of ${total}`} />
      </div>

      {/* Content */}
      <main className="relative z-10 flex-1 flex items-start justify-center px-4 py-8">
        <div className="w-full max-w-3xl space-y-5">

          {loading ? (
            <div className="card p-16 flex flex-col items-center gap-4">
              <Spinner size={32} />
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                Loading question…
              </p>
            </div>
          ) : question ? (
            <>
              {/* Question card */}
              <div className="card p-7 space-y-4 animate-fade-up">
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5"
                    style={{ background: isAdaptive ? 'rgba(245,158,11,0.1)' : 'rgba(61,90,255,0.1)' }}>
                    {isAdaptive
                      ? <Zap size={18} style={{ color: '#f59e0b' }} />
                      : <MessageSquare size={18} style={{ color: 'var(--accent)' }} />
                    }
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold uppercase tracking-widest"
                        style={{ color: isAdaptive ? '#f59e0b' : 'var(--accent)' }}>
                        {isAdaptive ? 'Follow-up' : `Question ${questionNumber}`}
                      </span>
                    </div>
                    <p className="text-lg leading-relaxed font-medium" style={{ color: 'var(--text-primary)' }}>
                      {question.question_text}
                    </p>
                  </div>
                </div>

                {/* Hint */}
                <div className="flex items-start gap-2 pt-2 border-t" style={{ borderColor: 'var(--border)' }}>
                  <Lightbulb size={14} className="mt-0.5 shrink-0" style={{ color: 'var(--text-muted)' }} />
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    Think out loud. Explain your reasoning, mention trade-offs, and reference real experience where possible.
                  </p>
                </div>
              </div>

              {/* Answer */}
              {!submitted ? (
                <div className="space-y-3 animate-fade-up animate-delay-100">
                  <div className="relative">
                    <textarea
                      ref={textareaRef}
                      className="textarea w-full min-h-[180px] text-sm leading-relaxed"
                      placeholder="Type your answer here… (Ctrl+Enter to submit)"
                      value={answer}
                      onChange={(e) => { setAnswer(e.target.value); setError('') }}
                      onKeyDown={handleKeyDown}
                    />
                    <div className="absolute bottom-3 right-3 text-xs font-mono"
                      style={{ color: answer.length > 50 ? 'var(--text-muted)' : 'var(--text-muted)', opacity: 0.6 }}>
                      {answer.length} chars
                    </div>
                  </div>

                  <ErrorBanner message={error} onDismiss={() => setError('')} />

                  <button
                    className="btn-primary w-full py-3.5"
                    onClick={handleSubmit}
                    disabled={submitting || !answer.trim()}
                  >
                    {submitting
                      ? <><Spinner size={16} className="text-white" /> Submitting…</>
                      : <><Send size={16} /> Submit Answer</>
                    }
                  </button>
                </div>
              ) : (
                /* Answer submitted state */
                <div className="space-y-4 animate-fade-up">
                  <div className="card p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-2 h-2 rounded-full" style={{ background: '#22c55e' }} />
                      <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: '#22c55e' }}>
                        Your Answer
                      </span>
                    </div>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--text-secondary)' }}>
                      {answer}
                    </p>
                  </div>

                  <button
                    className="btn-primary w-full py-3.5"
                    onClick={handleNext}
                  >
                    {nextAvailable
                      ? <><ChevronRight size={18} /> Next Question</>
                      : <><ChevronRight size={18} /> View My Results</>
                    }
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="card p-12 text-center space-y-3">
              <p className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                Interview Complete!
              </p>
              <button className="btn-primary" onClick={() =>
                navigate('/summary', { state: { sessionId, role, candidateData } })
              }>
                View Results
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}