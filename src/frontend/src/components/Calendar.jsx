import { useEffect, useState } from 'react'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { listEventDates } from '../api/eventDates.js'
import { listEvents } from '../api/events.js'
import StaffingBadge from './StaffingBadge.jsx'

export default function Calendar({ instructorId }) {
  const [calEvents, setCalEvents] = useState([])
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    Promise.all([
      listEventDates(instructorId ? { instructor_id: instructorId } : {}),
      listEvents(),
    ]).then(([eventDates, events]) => {
      const eventsById = Object.fromEntries(events.map(e => [e.id, e]))
      setCalEvents(
        eventDates.map(ed => ({
          id: String(ed.id),
          title: eventsById[ed.event_id]?.title || `Event ${ed.event_id}`,
          start: ed.start_time,
          end: ed.end_time,
          extendedProps: { eventDateId: ed.id, location: eventsById[ed.event_id]?.location },
        }))
      )
    })
  }, [instructorId])

  return (
    <div className="card">
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay',
        }}
        events={calEvents}
        eventClick={({ event }) => setSelected(event.extendedProps.eventDateId)}
        height="auto"
      />
      {selected && (
        <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#f0f4ff', borderRadius: 6 }}>
          <strong>Event Date #{selected} — Staffing</strong>
          <div style={{ marginTop: '0.5rem' }}>
            <StaffingBadge eventDateId={selected} />
          </div>
          <button
            style={{ marginTop: '0.5rem', fontSize: '0.8rem', cursor: 'pointer' }}
            onClick={() => setSelected(null)}
          >
            close
          </button>
        </div>
      )}
    </div>
  )
}
