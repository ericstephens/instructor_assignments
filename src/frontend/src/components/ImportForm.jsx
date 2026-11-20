import { useRef, useState } from 'react'
import client from '../api/client.js'

export default function ImportForm({ onSuccess }) {
  const [mode, setMode] = useState('append')
  const [file, setFile] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)   // { count, error }
  const fileRef = useRef()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) return
    setSubmitting(true)
    setResult(null)
    const form = new FormData()
    form.append('mode', mode)
    form.append('file', file)
    try {
      const r = await client.post('/events/import', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult({ count: r.data.length })
      setFile(null)
      fileRef.current.value = ''
      onSuccess && onSuccess()
    } catch (err) {
      setResult({ error: err.response?.data?.detail || 'Import failed.' })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="card">
      <h3>Import Event Catalog</h3>
      <p style={{ fontSize: '0.82rem', color: '#6b7280', marginBottom: '0.75rem' }}>
        CSV must include: title, description, duration, min_primary_instructors,
        min_secondary_instructors, max_students, location, catalog_status
      </p>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label id="import-mode-label">Import Mode</label>
          <div className="radio-group" aria-labelledby="import-mode-label">
            <label>
              <input type="radio" name="mode" value="append" checked={mode === 'append'} onChange={() => setMode('append')} />
              Append (keep existing)
            </label>
            <label>
              <input type="radio" name="mode" value="replace" checked={mode === 'replace'} onChange={() => setMode('replace')} />
              Replace (clear catalog first)
            </label>
          </div>
        </div>
        <div className="form-group">
          <label htmlFor="import-file">CSV File</label>
          <input
            id="import-file"
            type="file"
            accept=".csv,text/csv"
            ref={fileRef}
            onChange={e => setFile(e.target.files[0] || null)}
            required
          />
        </div>
        {result?.error && <p className="error-msg">{result.error}</p>}
        {result?.count != null && (
          <p className="success-msg">Imported {result.count} event{result.count !== 1 ? 's' : ''}.</p>
        )}
        <button type="submit" className="btn btn-primary" disabled={submitting || !file}>
          {submitting ? 'Importing…' : 'Import'}
        </button>
      </form>
    </div>
  )
}
