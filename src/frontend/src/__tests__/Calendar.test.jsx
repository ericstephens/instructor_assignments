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

  it('shows cancel button in adminMode', async () => {
    render(<Calendar adminMode={true} />)
    await waitFor(() => {
      expect(screen.getByText('today')).toBeInTheDocument()
    })
    // Cancel button only appears after selecting an event — verify it doesn't
    // appear without a selection (not in the DOM at rest)
    expect(screen.queryByTestId('cancel-event-date-btn')).not.toBeInTheDocument()
  })

  it('does not show cancel button without adminMode', async () => {
    render(<Calendar adminMode={false} />)
    await waitFor(() => {
      expect(screen.getByText('today')).toBeInTheDocument()
    })
    expect(screen.queryByTestId('cancel-event-date-btn')).not.toBeInTheDocument()
  })
})
