import { useState } from 'react'
import InstructorDashboard from './pages/InstructorDashboard.jsx'
import AdminDashboard from './pages/AdminDashboard.jsx'

const TABS = [
  { id: 'instructor', label: 'Instructor View' },
  { id: 'admin', label: 'Admin View' },
]

export default function App() {
  const [tab, setTab] = useState('instructor')

  return (
    <div className="container">
      <h1>Instructor Reservation System</h1>
      <div className="tabs">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`tab-btn ${tab === t.id ? 'active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === 'instructor' ? <InstructorDashboard /> : <AdminDashboard />}
    </div>
  )
}
