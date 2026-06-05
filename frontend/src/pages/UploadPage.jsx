import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Upload, FileText, CheckCircle2, ChevronRight,
  Cpu, Server, BarChart3, X, AlertCircle
} from 'lucide-react'
import { uploadResume, startInterview } from '../services/api'
import { Logo, Spinner, ErrorBanner, StepIndicator } from '../components/UI'

const ROLES = [
  {
    id: 'AI/ML Engineer',
    label: 'AI / ML Engineer',
    icon: Cpu,
    desc: 'Machine learning, deep learning, model deployment & MLOps',
    color: '#6366f1',
    glow: 'rgba(99,102,241,0.2)',
  },
  {
    id: 'Backend Engineer',
    label: 'Backend Engineer',
    icon: Server,
    desc: 'APIs, databases, system design & cloud infrastructure',
    color: '#06b6d4',
    glow: 'rgba(6,182,212,0.2)',
  },
  {
    id: 'Data Scientist',
    label: 'Data Scientist',
    icon: BarChart3,
    desc: 'Statistical analysis, modelling, A/B testing & insights',
    color: '#10b981',
    glow: 'rgba(16,185,129,0.2)',
  },
]

const STEPS = ['Upload Resume', 'Select Role', 'Start Interview']

export default function UploadPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [step, setStep] = useState(0)           // 0: upload, 1: role select, 2: starting
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [candidateData, setCandidateData] = useState(null)  // { candidate_id, skills, name }
  const [selectedRole, setSelectedRole] = useState(null)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')

  // ── Drag & Drop ─────────────────────────────────────────────────────────────
  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped?.type === 'application/pdf') {
      setFile(dropped)
      setError('')
    } else {
      setError('Please upload a PDF file.')
    }
  }, [])

  const handleDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const handleDragLeave = () => setDragging(false)

  const handleFileChange = (e) => {
    const picked = e.target.files[0]
    if (picked?.type === 'application/pdf') {
      setFile(picked)
      setError('')
    } else {
      setError('Please upload a PDF file.')
    }
  }

  // ── Upload ──────────────────────────────────────────────────────────────────
  const handleUpload = async () => {
    if (!file) return setError('Please select a PDF resume.')
    setUploading(true)
    setError('')
    try {
      const data = await uploadResume(file)
      setCandidateData(data)
      setStep(1)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  // ── Start Interview ─────────────────────────────────────────────────────────
  const handleStart = async () => {
    if (!selectedRole) return setError('Please select a role.')
    setStarting(true)
    setError('')
    try {
      const data = await startInterview(candidateData.candidate_id, selectedRole)
      navigate('/interview', {
        state: {
          sessionId: data.session_id,
          role: data.role,
          totalQuestions: data.total_questions,
          candidateData,
        },
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setStarting(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-primary)' }}>
      {/* Background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full opacity-10 blur-[120px]"
          style={{ background: 'radial-gradient(circle, #3d5aff, transparent)' }} />
        <div className="absolute -bottom-40 -right-40 w-[500px] h-[500px] rounded-full opacity-8 blur-[120px]"
          style={{ background: 'radial-gradient(circle, #7c3aed, transparent)' }} />
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-8 py-5 border-b"
        style={{ borderColor: 'var(--border)' }}>
        <Logo />
        <StepIndicator steps={STEPS} current={step} />
        <div className="w-28" /> {/* Spacer */}
      </header>

      {/* Main */}
      <main className="relative z-10 flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-2xl space-y-6">

          {/* ── STEP 0: Upload ── */}
          {step === 0 && (
            <div className="space-y-6 animate-fade-up">
              <div className="space-y-2">
                <h1 className="text-4xl font-display gradient-text">Upload Your Resume</h1>
                <p className="text-base" style={{ color: 'var(--text-secondary)' }}>
                  Our AI will parse your resume and generate a personalised technical interview.
                </p>
              </div>

              {/* Drop zone */}
              <div
                className={`relative flex flex-col items-center justify-center gap-4 p-12 rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-300 ${
                  dragging ? 'border-blue-500 scale-[1.01]' : 'hover:border-white/20'
                } ${file ? 'border-green-500/40' : ''}`}
                style={{
                  borderColor: dragging ? 'var(--accent)' :
                    file ? 'rgba(34,197,94,0.4)' : 'var(--border)',
                  background: dragging ? 'rgba(61,90,255,0.05)' :
                    file ? 'rgba(34,197,94,0.04)' : 'var(--bg-card)',
                  boxShadow: dragging ? '0 0 0 4px var(--accent-glow)' : 'none',
                }}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => !file && fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={handleFileChange}
                />

                {file ? (
                  <>
                    <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                      style={{ background: 'rgba(34,197,94,0.1)' }}>
                      <FileText size={32} style={{ color: '#22c55e' }} />
                    </div>
                    <div className="text-center">
                      <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>{file.name}</p>
                      <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                    <button
                      className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-all"
                      style={{ color: 'var(--text-secondary)', background: 'rgba(255,255,255,0.05)' }}
                      onClick={(e) => { e.stopPropagation(); setFile(null) }}
                    >
                      <X size={12} /> Remove
                    </button>
                  </>
                ) : (
                  <>
                    <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                      style={{ background: 'rgba(61,90,255,0.1)' }}>
                      <Upload size={28} style={{ color: 'var(--accent)' }} />
                    </div>
                    <div className="text-center">
                      <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                        Drop your resume here
                      </p>
                      <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                        or click to browse — PDF only, max 10 MB
                      </p>
                    </div>
                  </>
                )}
              </div>

              <ErrorBanner message={error} onDismiss={() => setError('')} />

              <button
                className="btn-primary w-full text-base py-4"
                onClick={handleUpload}
                disabled={!file || uploading}
              >
                {uploading ? (
                  <><Spinner size={18} className="text-white" /> Parsing Resume…</>
                ) : (
                  <><Upload size={18} /> Upload & Analyse Resume</>
                )}
              </button>
            </div>
          )}

          {/* ── STEP 1: Role Selection ── */}
          {step === 1 && candidateData && (
            <div className="space-y-6 animate-fade-up">
              {/* Skills summary */}
              <div className="card p-5 space-y-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={18} style={{ color: '#22c55e' }} />
                  <span className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
                    Resume Parsed Successfully
                  </span>
                  {candidateData.name && (
                    <span className="text-sm ml-auto" style={{ color: 'var(--text-secondary)' }}>
                      {candidateData.name}
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {candidateData.skills.slice(0, 18).map((s) => (
                    <span key={s} className="skill-chip">{s}</span>
                  ))}
                  {candidateData.skills.length > 18 && (
                    <span className="skill-chip">+{candidateData.skills.length - 18} more</span>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <h1 className="text-4xl font-display gradient-text">Select Your Role</h1>
                <p className="text-base" style={{ color: 'var(--text-secondary)' }}>
                  Choose the position you're interviewing for.
                </p>
              </div>

              <div className="space-y-3">
                {ROLES.map((role) => {
                  const Icon = role.icon
                  const active = selectedRole === role.id
                  return (
                    <button
                      key={role.id}
                      className="w-full flex items-center gap-4 p-5 rounded-2xl border text-left transition-all duration-200"
                      style={{
                        background: active ? `${role.glow}` : 'var(--bg-card)',
                        borderColor: active ? role.color : 'var(--border)',
                        boxShadow: active ? `0 0 20px ${role.glow}` : 'none',
                        transform: active ? 'scale(1.01)' : 'scale(1)',
                      }}
                      onClick={() => { setSelectedRole(role.id); setError('') }}
                    >
                      <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
                        style={{ background: `${role.glow}`, border: `1px solid ${role.color}30` }}>
                        <Icon size={22} style={{ color: role.color }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold" style={{ color: active ? role.color : 'var(--text-primary)' }}>
                          {role.label}
                        </p>
                        <p className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>
                          {role.desc}
                        </p>
                      </div>
                      <div className={`w-5 h-5 rounded-full border-2 shrink-0 flex items-center justify-center transition-all`}
                        style={{
                          borderColor: active ? role.color : 'var(--border)',
                          background: active ? role.color : 'transparent',
                        }}>
                        {active && <CheckCircle2 size={12} className="text-white" />}
                      </div>
                    </button>
                  )
                })}
              </div>

              <ErrorBanner message={error} onDismiss={() => setError('')} />

              <button
                className="btn-primary w-full text-base py-4"
                onClick={handleStart}
                disabled={!selectedRole || starting}
              >
                {starting ? (
                  <><Spinner size={18} className="text-white" /> Generating Questions…</>
                ) : (
                  <>Begin Interview <ChevronRight size={18} /></>
                )}
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}