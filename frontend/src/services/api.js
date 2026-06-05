import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000, // 60s for LLM calls
})

// ── Interceptors ──────────────────────────────────────────────────────────────

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred.'
    return Promise.reject(new Error(message))
  }
)

// ── API methods ───────────────────────────────────────────────────────────────

export const uploadResume = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/upload-resume', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export const startInterview = async (candidateId, role) => {
  const { data } = await api.post('/start-interview', {
    candidate_id: candidateId,
    role,
  })
  return data
}

export const getQuestion = async (sessionId) => {
  const { data } = await api.get(`/question/${sessionId}`)
  return data
}

export const submitAnswer = async (sessionId, questionId, answerText) => {
  const { data } = await api.post('/answer', {
    session_id: sessionId,
    question_id: questionId,
    answer_text: answerText,
  })
  return data
}

export const getSummary = async (sessionId) => {
  const { data } = await api.get(`/summary/${sessionId}`)
  return data
}

export const downloadReport = (sessionId) => {
  window.open(`/api/v1/summary/${sessionId}/download`, '_blank')
}

export const getHealth = async () => {
  const { data } = await api.get('/health')
  return data
}

export const getCandidateSessions = async (candidateId) => {
  const { data } = await api.get(`/sessions/${candidateId}`)
  return data
}

export default api