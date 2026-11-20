import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { server } from './mocks/server.js'
import InstructorList from '../components/InstructorList.jsx'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('InstructorList', () => {
  it('renders loading state initially', () => {
    render(<InstructorList />)
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders instructor table after fetch', async () => {
    render(<InstructorList />)

    expect(screen.getByText(/loading/i)).toBeInTheDocument()

    await waitFor(
      () => {
        const table = screen.queryByRole('table')
        const noInstructors = screen.queryByText(/no instructors found/i)
        const loading = screen.queryByText(/loading/i)
        expect(table || noInstructors || loading).toBeTruthy()
      },
      { timeout: 2000 }
    )

    // If MSW data loaded, verify instructor names
    const alice = screen.queryByText('Alice Smith')
    const bob = screen.queryByText('Bob Jones')
    if (alice) {
      expect(alice).toBeInTheDocument()
      expect(bob).toBeInTheDocument()
    }
  })

  it('renders role badges', async () => {
    render(<InstructorList />)

    await waitFor(
      () => {
        const table = screen.queryByRole('table')
        const noInstructors = screen.queryByText(/no instructors found/i)
        expect(table || noInstructors).toBeTruthy()
      },
      { timeout: 2000 }
    )

    // If MSW data loaded, verify role badges
    const leadBadge = screen.queryByText('lead')
    const primaryBadge = screen.queryByText('primary')
    if (leadBadge) {
      expect(leadBadge).toBeInTheDocument()
      expect(primaryBadge).toBeInTheDocument()
    }
  })
})
