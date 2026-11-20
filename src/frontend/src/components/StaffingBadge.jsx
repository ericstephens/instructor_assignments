import { useEffect, useState } from 'react'
import { getStaffingStatus } from '../api/eventDates.js'

export default function StaffingBadge({ eventDateId }) {
  const [status, setStatus] = useState(null)

  useEffect(() => {
    if (!eventDateId) return
    getStaffingStatus(eventDateId).then(setStatus).catch(() => setStatus(null))
  }, [eventDateId])

  if (!status) return null

  return (
    <div className="staffing-row" data-testid="staffing-badge">
      <span className={`badge ${status.lead_assigned ? 'badge-ok' : 'badge-warn'}`}>
        Lead: {status.lead_assigned ? '✓' : '✗'}
      </span>
      <span className={`badge ${status.primary_met ? 'badge-ok' : 'badge-warn'}`}>
        Primary: {status.primary_count}/{status.min_primary_instructors}
      </span>
      <span className={`badge ${status.secondary_met ? 'badge-ok' : 'badge-warn'}`}>
        Secondary: {status.secondary_count}/{status.min_secondary_instructors}
      </span>
    </div>
  )
}
