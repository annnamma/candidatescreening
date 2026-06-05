import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import UploadPage from './pages/UploadPage'
import InterviewPage from './pages/InterviewPage'
import SummaryPage from './pages/SummaryPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/interview" element={<InterviewPage />} />
        <Route path="/summary" element={<SummaryPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}