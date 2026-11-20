import { useEffect, useState, useCallback } from 'react'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { listEventDates, cancelEventDate } from '../api/eventDates.js'
import { listEvents } from '../api/events.js'
import StaffingBadge from './StaffingBadge.jsx'

export default function Calendar({ instructorId, adminMode = false, onCancelled }) {
  const [calEvents, setCalEvents] = useState([])
  const [selected, setSelected] = useState(null)   // { eventDateId, isCancelled }
  const [cancelling, setCancelling] = useState(false)
  const [cancelError, setCancelError] = useState(null)

  const load = useCallback(() => {
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
          backgroundColor: ed.is_cancelled ? '#9ca3af' : undefined,
          borderColor: ed.is_cancelled ? '#6b7280' : undefined,
          textColor: ed.is_cancelled ? '#fff' : undefined,
          extendedProps: {
            eventDateId: ed.id,
            isCancelled: ed.is_cancelled,
            location: eventsById[ed.event_id]?.location,
          },
        }))
      )
    })
  }, [instructorId])

  useEffect(() => { load() }, [load])

  const handleCancel = async () => {
    if (!selected) return
    setCancelling(true)
    setCancelError(null)
    try {
      await cancelEventDate(selected.eventDateId)
      setSelected(null)
      load()
      onCancelled && onCancelled()
    } catch (err) {
      setCancelError(err.response?.data?.detail || 'Cancel failed.')
    } finally {
      setCancelling(false)
    }
  }

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
        eventClick={({ event }) => {
          setSelected({
            eventDateId: event.extendedProps.eventDateId,
            isCancelled: event.extendedProps.isCancelled,
          })
          setCancelError(null)
        }}
        height="auto"
      />
      {selected && (
        <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#f0f4ff', borderRadius: 6 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong>
              Event Date #{selected.eventDateId}
              {selected.isCancelled && (
                <span className="badge badge-warn" style={{ marginLeft: '0.5rem' }}>CANCELLED</span>
              )}
            </strong>
            <button style={{ fontSize: '0.8rem', cursor: 'pointer', border: 'none', background: 'none' }} onClick={() => setSelected(null)}>✕</button>
          </div>
          {!selected.isCancelled && (
            <div style={{ marginTop: '0.5rem' }}>
              <StaffingBadge eventDateId={selected.eventDateId} />
            </div>
          )}
          {adminMode && !selected.isCancelled && (
            <div style={{ marginTop: '0.75rem' }}>
              <button
                className="btn btn-danger"
                onClick={handleCancel}
                disabled={cancelling}
                data-testid="cancel-event-date-btn"
              >
                {cancelling ? 'Cancelling…' : 'Cancel Event Date'}
              </button>
              {cancelError && <p className="error-msg">{cancelError}</p>}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
