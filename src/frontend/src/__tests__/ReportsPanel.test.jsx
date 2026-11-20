import { render, screen } from '@testing-library/react'
import { beforeAll, afterEach, afterAll, describe, it, expect } from 'vitest'
import { server } from './mocks/server.js'
import ReportsPanel from '../components/ReportsPanel.jsx'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('ReportsPanel', () => {
  it('renders Instructor History tab by default', () => {
    render(<ReportsPanel />)
    expect(screen.getByText('Instructor Allocation History')).toBeInTheDocument()
  })

  it('renders tab switcher with both report types', () => {
    render(<ReportsPanel />)
    expect(screen.getByRole('button', { name: 'Instructor History' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Class Schedule' })).toBeInTheDocument()
  })

  it('renders Run button', () => {
    render(<ReportsPanel />)
    expect(screen.getByRole('button', { name: 'Run' })).toBeInTheDocument()
  })
})
