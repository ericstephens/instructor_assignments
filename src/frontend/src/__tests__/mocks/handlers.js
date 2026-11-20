import { http, HttpResponse } from 'msw'

const BASE = 'http://localhost:8000'

export const handlers = [
  http.get(`${BASE}/event-dates`, () =>
    HttpResponse.json([
      {
        id: 1,
        event_id: 1,
        date: '2026-04-01T00:00:00',
        start_time: '2026-04-01T09:00:00',
        end_time: '2026-04-01T17:00:00',
        lead_instructor_id: null,
        registered_students: 5,
        is_cancelled: false,
      },
    ])
  ),

  http.get(`${BASE}/events`, () =>
    HttpResponse.json([
      {
        id: 1,
        title: 'Python 101',
        description: 'Intro course',
        duration: 1,
        min_primary_instructors: 1,
        min_secondary_instructors: 1,
        max_students: 20,
        location: 'Room A',
        catalog_status: 'active',
      },
    ])
  ),

  http.get(`${BASE}/instructors`, () =>
    HttpResponse.json([
      { id: 1, name: 'Alice Smith', email: 'alice@example.com', role: 'lead' },
      { id: 2, name: 'Bob Jones', email: 'bob@example.com', role: 'primary' },
    ])
  ),

  http.get(`${BASE}/event-dates/:id/staffing-status`, ({ params }) =>
    HttpResponse.json({
      event_date_id: Number(params.id),
      lead_assigned: true,
      lead_instructor_id: 1,
      primary_count: 1,
      min_primary_instructors: 2,
      primary_met: false,
      secondary_count: 0,
      min_secondary_instructors: 1,
      secondary_met: false,
    })
  ),

  http.post(`${BASE}/allocations`, () =>
    HttpResponse.json(
      { id: 99, event_date_id: 1, instructor_id: 2, shift_duration: 8, role: 'primary' },
      { status: 201 }
    )
  ),

  http.post(`${BASE}/event-dates/:id/cancel`, ({ params }) =>
    HttpResponse.json({
      id: Number(params.id),
      event_id: 1,
      date: '2026-04-01T00:00:00',
      start_time: '2026-04-01T09:00:00',
      end_time: '2026-04-01T17:00:00',
      lead_instructor_id: null,
      registered_students: 0,
      is_cancelled: true,
    })
  ),

  http.post(`${BASE}/events/import`, () =>
    HttpResponse.json(
      [{ id: 10, title: 'Imported Event', duration: 1, min_primary_instructors: 1,
         min_secondary_instructors: 0, max_students: 20, location: 'Room Z', catalog_status: 'active' }],
      { status: 201 }
    )
  ),

  http.get(`${BASE}/reports/instructor-history`, () =>
    HttpResponse.json([
      { allocation_id: 1, event_date_id: 1, event_id: 1, event_title: 'Python 101',
        date: '2026-04-01T00:00:00', start_time: '2026-04-01T09:00:00',
        end_time: '2026-04-01T17:00:00', role: 'primary', shift_duration: 8 },
    ])
  ),

  http.get(`${BASE}/reports/class-schedule`, () =>
    HttpResponse.json([
      { event_date_id: 1, event_id: 1, event_title: 'Python 101', location: 'Room A',
        date: '2026-04-01T00:00:00', start_time: '2026-04-01T09:00:00',
        end_time: '2026-04-01T17:00:00', registered_students: 5, lead_assigned: true,
        allocation_count: 2 },
    ])
  ),
]
