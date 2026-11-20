import { useEffect, useState } from 'react'
import { listInstructors } from '../api/instructors.js'

export default function InstructorList() {
  const [instructors, setInstructors] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listInstructors()
      .then(setInstructors)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading instructors…</p>
  if (!instructors.length) return <p>No instructors found.</p>

  return (
    <div className="card">
      <h3>Instructors</h3>
      <table>
        <thead>
          <tr><th>Name</th><th>Email</th><th>Role</th></tr>
        </thead>
        <tbody>
          {instructors.map(i => (
            <tr key={i.id}>
              <td>{i.name}</td>
              <td>{i.email}</td>
              <td><span className={`badge badge-${i.role}`}>{i.role}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
