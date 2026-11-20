import { useState } from 'react'
import EventList from '../components/EventList.jsx'
import InstructorList from '../components/InstructorList.jsx'
import AllocationForm from '../components/AllocationForm.jsx'
import Calendar from '../components/Calendar.jsx'
import ImportForm from '../components/ImportForm.jsx'
import ReportsPanel from '../components/ReportsPanel.jsx'

const ADMIN_TABS = [
  { id: 'schedule', label: 'Schedule' },
  { id: 'assign', label: 'Assign' },
  { id: 'import', label: 'Import' },
  { id: 'reports', label: 'Reports' },
]

export default function AdminDashboard() {
  const [tab, setTab] = useState('schedule')
  const [calendarKey, setCalendarKey] = useState(0)

  const refresh = () => setCalendarKey(k => k + 1)

  return (
    <div>
      <h2>Admin Dashboard</h2>
      <div className="tabs">
        {ADMIN_TABS.map(t => (
          <button
            key={t.id}
            className={`tab-btn ${tab === t.id ? 'active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'schedule' && (
        <>
          <Calendar key={calendarKey} adminMode={true} onCancelled={refresh} />
          <div className="two-col">
            <EventList />
            <InstructorList />
          </div>
        </>
      )}

      {tab === 'assign' && (
        <AllocationForm onSuccess={refresh} />
      )}

      {tab === 'import' && (
        <ImportForm onSuccess={refresh} />
      )}

      {tab === 'reports' && (
        <ReportsPanel />
      )}
    </div>
  )
}
