import { useEffect, useState } from 'react'
import { listInstructors } from '../api/instructors.js'
import client from '../api/client.js'

function InstructorHistoryReport() {
  const [instructors, setInstructors] = useState([])
  const [instructorId, setInstructorId] = useState('')
  const [rows, setRows] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    listInstructors().then(list => {
      setInstructors(list)
      if (list.length) setInstructorId(String(list[0].id))
    })
  }, [])

  const run = async () => {
    if (!instructorId) return
    setLoading(true)
    try {
      const r = await client.get('/reports/instructor-history', { params: { instructor_id: instructorId } })
      setRows(r.data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h3>Instructor Allocation History</h3>
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end', marginBottom: '1rem' }}>
        <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
          <label htmlFor="history-instructor">Instructor</label>
          <select id="history-instructor" value={instructorId} onChange={e => setInstructorId(e.target.value)}>
            {instructors.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
          </select>
        </div>
        <button className="btn btn-primary" onClick={run} disabled={loading || !instructorId}>
          {loading ? 'Loading…' : 'Run'}
        </button>
      </div>
      {rows && (rows.length === 0
        ? <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>No allocations found.</p>
        : (
          <table>
            <thead>
              <tr><th>Event</th><th>Date</th><th>Role</th><th>Shift</th></tr>
            </thead>
            <tbody>
              {rows.map(r => (
                <tr key={r.allocation_id}>
                  <td>{r.event_title}</td>
                  <td>{new Date(r.date).toLocaleDateString()}</td>
                  <td><span className={`badge badge-${r.role}`}>{r.role}</span></td>
                  <td>{r.shift_duration}h</td>
                </tr>
              ))}
            </tbody>
          </table>
        )
      )}
    </div>
  )
}

function ClassScheduleReport() {
  const [rows, setRows] = useState(null)
  const [loading, setLoading] = useState(false)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const run = async () => {
    setLoading(true)
    try {
      const params = {}
      if (dateFrom) params.date_from = new Date(dateFrom).toISOString()
      if (dateTo) params.date_to = new Date(dateTo).toISOString()
      const r = await client.get('/reports/class-schedule', { params })
      setRows(r.data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h3>Class Schedule</h3>
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label htmlFor="sched-from">From</label>
          <input id="sched-from" type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
        </div>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label htmlFor="sched-to">To</label>
          <input id="sched-to" type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} />
        </div>
        <button className="btn btn-primary" onClick={run} disabled={loading}>
          {loading ? 'Loading…' : 'Run'}
        </button>
      </div>
      {rows && (rows.length === 0
        ? <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>No events found.</p>
        : (
          <table>
            <thead>
              <tr><th>Event</th><th>Location</th><th>Date</th><th>Students</th><th>Allocations</th><th>Lead</th></tr>
            </thead>
            <tbody>
              {rows.map(r => (
                <tr key={r.event_date_id}>
                  <td>{r.event_title}</td>
                  <td>{r.location}</td>
                  <td>{new Date(r.date).toLocaleDateString()}</td>
                  <td>{r.registered_students}</td>
                  <td>{r.allocation_count}</td>
                  <td>{r.lead_assigned ? '✓' : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )
      )}
    </div>
  )
}

export default function ReportsPanel() {
  const [tab, setTab] = useState('history')
  return (
    <div>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        {[['history', 'Instructor History'], ['schedule', 'Class Schedule']].map(([id, label]) => (
          <button
            key={id}
            className={`tab-btn ${tab === id ? 'active' : ''}`}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>
      {tab === 'history' ? <InstructorHistoryReport /> : <ClassScheduleReport />}
    </div>
  )
}
