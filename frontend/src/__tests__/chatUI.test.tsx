import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ChatUI from '../components/chat/ChatUI'
import { api } from '../lib/api'

jest.mock('../lib/api', () => ({
  api: {
    post: jest.fn(),
  },
}))

jest.mock('../components/MarkdownViewer', () => ({
  __esModule: true,
  default: ({ content }: { content: string }) => <div>{content}</div>,
}))

describe('ChatUI', () => {
  it('sends message and displays response', async () => {
    ;(api.post as jest.Mock).mockResolvedValueOnce({
      data: { session_id: 1, answer: 'Hello from bot' },
    })

    render(<ChatUI />)

    fireEvent.change(screen.getByPlaceholderText('Repository ID'), {
      target: { value: '1' },
    })
    fireEvent.change(screen.getByPlaceholderText('Ask a question about the code...'), {
      target: { value: 'What is this repo?' },
    })

    fireEvent.click(screen.getByText('Send'))

    await waitFor(() => {
      expect(screen.getByText('Hello from bot')).toBeInTheDocument()
    })
  })
})
