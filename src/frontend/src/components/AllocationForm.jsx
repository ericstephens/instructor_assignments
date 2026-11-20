import { useEffect, useState } from 'react'
import { listEventDates } from '../api/eventDates.js'
import { listInstructors } from '../api/instructors.js'
import { createAllocation } from '../api/allocations.js'

export default function AllocationForm({ onSuccess }) {
  const [eventDates, setEventDates] = useState([])
  const [instructors, setInstructors] = useState([])
  const [form, setForm] = useState({
    event_date_id: '',
    instructor_id: '',
    role: 'primary',
    shift_duration: 8,
  })
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    listEventDates().then(setEventDates)
    listInstructors().then(setInstructors)
  }, [])

  const handleChange = (field, value) =>
    setForm(f => ({ ...f, [field]: value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)
    setSubmitting(true)
    try {
      await createAllocation({
        event_date_id: Number(form.event_date_id),
        instructor_id: Number(form.instructor_id),
        role: form.role,
        shift_duration: Number(form.shift_duration),
      })
      setSuccess(true)
      setForm({ event_date_id: '', instructor_id: '', role: 'primary', shift_duration: 8 })
      onSuccess && onSuccess()
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(detail || 'Failed to create allocation.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="card">
      <h3>Assign Instructor</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="event-date-select">Event Date</label>
          <select
            id="event-date-select"
            value={form.event_date_id}
            onChange={e => handleChange('event_date_id', e.target.value)}
            required
          >
            <option value="">— select —</option>
            {eventDates.map(ed => (
              <option key={ed.id} value={ed.id}>
                {new Date(ed.start_time).toLocaleString()} (ID {ed.id})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="instructor-select">Instructor</label>
          <select
            id="instructor-select"
            value={form.instructor_id}
            onChange={e => handleChange('instructor_id', e.target.value)}
            required
          >
            <option value="">— select —</option>
            {instructors.map(i => (
              <option key={i.id} value={i.id}>{i.name} ({i.role})</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label id="role-label">Role</label>
          <div className="radio-group" aria-labelledby="role-label">
            {['lead', 'primary', 'secondary'].map(r => (
              <label key={r}>
                <input
                  type="radio"
                  name="role"
                  value={r}
                  checked={form.role === r}
                  onChange={() => handleChange('role', r)}
                />
                {r}
              </label>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label id="shift-label">Shift Duration</label>
          <div className="radio-group" aria-labelledby="shift-label">
            <label>
              <input
                type="radio"
                name="shift_duration"
                value={4}
                checked={Number(form.shift_duration) === 4}
                onChange={() => handleChange('shift_duration', 4)}
              />
              Half day (4h)
            </label>
            <label>
              <input
                type="radio"
                name="shift_duration"
                value={8}
                checked={Number(form.shift_duration) === 8}
                onChange={() => handleChange('shift_duration', 8)}
              />
              Full day (8h)
            </label>
          </div>
        </div>

        {error && <p className="error-msg" role="alert">{error}</p>}
        {success && <p className="success-msg">Allocation created successfully.</p>}

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Saving…' : 'Assign'}
        </button>
      </form>
    </div>
  )
}
