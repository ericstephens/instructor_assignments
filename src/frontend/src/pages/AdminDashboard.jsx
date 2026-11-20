import { useState } from 'react'
import EventList from '../components/EventList.jsx'
import InstructorList from '../components/InstructorList.jsx'
import AllocationForm from '../components/AllocationForm.jsx'
import Calendar from '../components/Calendar.jsx'

export default function AdminDashboard() {
  const [calendarKey, setCalendarKey] = useState(0)

  const refresh = () => setCalendarKey(k => k + 1)

  return (
    <div>
      <h2>Admin Dashboard</h2>
      <Calendar key={calendarKey} adminMode={true} onCancelled={refresh} />
      <div className="two-col">
        <div>
          <EventList />
          <InstructorList />
        </div>
        <div>
          <AllocationForm onSuccess={refresh} />
        </div>
      </div>
    </div>
  )
}
