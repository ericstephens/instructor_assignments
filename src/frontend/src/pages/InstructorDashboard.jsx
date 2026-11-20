import { useEffect, useState } from 'react'
import Calendar from '../components/Calendar.jsx'
import { listInstructors } from '../api/instructors.js'

export default function InstructorDashboard() {
  const [instructors, setInstructors] = useState([])
  const [selectedId, setSelectedId] = useState('')

  useEffect(() => {
    listInstructors().then(list => {
      setInstructors(list)
      if (list.length) setSelectedId(String(list[0].id))
    })
  }, [])

  return (
    <div>
      <h2>Instructor Dashboard</h2>
      <div className="form-group" style={{ maxWidth: 300 }}>
        <label>Viewing as</label>
        <select value={selectedId} onChange={e => setSelectedId(e.target.value)}>
          <option value="">— all instructors —</option>
          {instructors.map(i => (
            <option key={i.id} value={i.id}>{i.name}</option>
          ))}
        </select>
      </div>
      <Calendar instructorId={selectedId ? Number(selectedId) : undefined} />
    </div>
  )
}
