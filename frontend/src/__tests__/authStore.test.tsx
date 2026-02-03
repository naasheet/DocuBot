import { act } from '@testing-library/react'
import { useAuthStore } from '../lib/store/authStore'
import { api } from '../lib/api'

jest.mock('../lib/api', () => ({
  api: {
    post: jest.fn(),
    get: jest.fn(),
  },
  setAuthToken: jest.fn(),
}))

describe('auth store', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    jest.clearAllMocks()
  })

  it('login stores token and user', async () => {
    ;(api.post as jest.Mock).mockResolvedValueOnce({ data: { access_token: 'token123' } })
    ;(api.get as jest.Mock).mockResolvedValueOnce({ data: { id: 1, email: 'test@example.com' } })

    await act(async () => {
      await useAuthStore.getState().login('test@example.com', 'password123', true)
    })

    expect(localStorage.getItem('token')).toBe('token123')
    expect(useAuthStore.getState().user?.email).toBe('test@example.com')
  })

  it('logout clears token and user', () => {
    localStorage.setItem('token', 'token123')
    useAuthStore.setState({ user: { id: 1, email: 'test@example.com' }, token: 'token123' })

    useAuthStore.getState().logout()

    expect(localStorage.getItem('token')).toBeNull()
    expect(useAuthStore.getState().user).toBeNull()
    expect(useAuthStore.getState().token).toBeNull()
  })
})
