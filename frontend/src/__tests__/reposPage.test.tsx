import { render, screen } from '@testing-library/react'
import ReposPage from '../app/repos/page'

jest.mock('../lib/hooks/useRepos', () => ({
  useRepos: () => ({
    repos: [
      { id: 1, full_name: 'test/repo', description: 'Test repo', private: false },
    ],
    loading: false,
    error: null,
  }),
}))

describe('ReposPage', () => {
  it('renders repo list', () => {
    render(<ReposPage />)
    expect(screen.getByText('test/repo')).toBeInTheDocument()
    expect(screen.getByText('Test repo')).toBeInTheDocument()
  })
})
