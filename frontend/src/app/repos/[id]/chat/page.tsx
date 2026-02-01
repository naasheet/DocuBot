export default function ChatPage({ params }: { params: { id: string } }) {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">Chat with Codebase</h1>
      <p>Chat interface for repository {params.id} will appear here.</p>
    </div>
  )
}
