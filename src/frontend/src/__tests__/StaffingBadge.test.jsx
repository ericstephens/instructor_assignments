import { render, screen, waitFor } from '@testing-library/react'
import { beforeAll, afterEach, afterAll, describe, it, expect } from 'vitest'
import { server } from './mocks/server.js'
import StaffingBadge from '../components/StaffingBadge.jsx'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('StaffingBadge', () => {
  it('renders lead/primary/secondary counts from API', async () => {
    render(<StaffingBadge eventDateId={1} />)

    await waitFor(() => {
      expect(screen.getByTestId('staffing-badge')).toBeInTheDocument()
    })

    expect(screen.getByText(/Lead: ✓/)).toBeInTheDocument()
    expect(screen.getByText(/Primary: 1\/2/)).toBeInTheDocument()
    expect(screen.getByText(/Secondary: 0\/1/)).toBeInTheDocument()
  })

  it('renders nothing when eventDateId is null', () => {
    const { container } = render(<StaffingBadge eventDateId={null} />)
    expect(container).toBeEmptyDOMElement()
  })
})
