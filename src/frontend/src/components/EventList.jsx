import { useEffect, useState } from 'react'
import { listEvents } from '../api/events.js'

export default function EventList({ onSelectEvent }) {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listEvents()
      .then(setEvents)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading events…</p>
  if (!events.length) return <p>No events found.</p>

  return (
    <div className="card">
      <h3>Events</h3>
      <table>
        <thead>
          <tr>
            <th>Title</th>
            <th>Duration</th>
            <th>Location</th>
            <th>Status</th>
            <th>Students</th>
          </tr>
        </thead>
        <tbody>
          {events.map(e => (
            <tr
              key={e.id}
              style={{ cursor: onSelectEvent ? 'pointer' : 'default' }}
              onClick={() => onSelectEvent && onSelectEvent(e)}
            >
              <td>{e.title}</td>
              <td>{e.duration}d</td>
              <td>{e.location}</td>
              <td>
                <span className={`badge badge-${e.catalog_status}`}>
                  {e.catalog_status}
                </span>
              </td>
              <td>{e.max_students}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
