import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { server } from './mocks/server.js'
import AdminDashboard from '../pages/AdminDashboard.jsx'
import InstructorDashboard from '../pages/InstructorDashboard.jsx'

// Mock FullCalendar and heavy calendar dependencies to keep dashboard smoke
// tests lightweight and avoid @fullcalendar rendering issues in jsdom
vi.mock('@fullcalendar/react', () => ({
  default: () => <div data-testid="fullcalendar-mock" />,
}))
vi.mock('@fullcalendar/daygrid', () => ({ default: {} }))
vi.mock('@fullcalendar/timegrid', () => ({ default: {} }))
vi.mock('@fullcalendar/interaction', () => ({ default: {} }))

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('AdminDashboard', () => {
  it('renders without crashing', () => {
    render(<AdminDashboard />)
    // At least one heading should be present
    const headings = screen.getAllByRole('heading')
    expect(headings.length).toBeGreaterThan(0)
  })
})

describe('InstructorDashboard', () => {
  it('renders without crashing', () => {
    render(<InstructorDashboard />)
    expect(screen.getByRole('heading', { name: /instructor dashboard/i })).toBeInTheDocument()
  })

  it('shows instructor selector', async () => {
    render(<InstructorDashboard />)

    // The "Viewing as" label is present in the initial render (not data-dependent)
    await waitFor(
      () => {
        expect(screen.getByText(/viewing as/i)).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })
})
