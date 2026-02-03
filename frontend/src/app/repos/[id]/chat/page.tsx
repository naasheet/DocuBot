import { redirect } from 'next/navigation'

export default function ChatPage({ params }: { params: { id: string } }) {
  redirect(`/chat?repoId=${params.id}`)
}
