import { render, screen } from '@testing-library/react'
import { beforeAll, afterEach, afterAll, describe, it, expect } from 'vitest'
import { server } from './mocks/server.js'
import ImportForm from '../components/ImportForm.jsx'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('ImportForm', () => {
  it('renders import mode radio buttons', () => {
    render(<ImportForm />)
    expect(screen.getByText('Import Event Catalog')).toBeInTheDocument()
    expect(screen.getByLabelText(/Append/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Replace/)).toBeInTheDocument()
  })

  it('renders file input', () => {
    render(<ImportForm />)
    expect(screen.getByLabelText('CSV File')).toBeInTheDocument()
  })

  it('submit button is disabled without file selected', () => {
    render(<ImportForm />)
    expect(screen.getByRole('button', { name: 'Import' })).toBeDisabled()
  })
})
