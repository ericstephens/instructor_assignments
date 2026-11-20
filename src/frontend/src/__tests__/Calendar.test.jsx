import { render, screen, waitFor } from '@testing-library/react'
import { beforeAll, afterEach, afterAll, describe, it, expect } from 'vitest'
import { server } from './mocks/server.js'
import Calendar from '../components/Calendar.jsx'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('Calendar', () => {
  it('mounts FullCalendar without crashing', async () => {
    render(<Calendar />)
    // FullCalendar renders navigation buttons
    await waitFor(() => {
      expect(screen.getByText('today')).toBeInTheDocument()
    })
  })

  it('renders month/week/day view controls', async () => {
    render(<Calendar />)
    await waitFor(() => {
      expect(screen.getByText('month')).toBeInTheDocument()
      expect(screen.getByText('week')).toBeInTheDocument()
      expect(screen.getByText('day')).toBeInTheDocument()
    })
  })
})
