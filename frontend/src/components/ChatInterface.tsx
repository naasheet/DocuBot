export default function ChatInterface() {
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4">
        {/* Messages will appear here */}
      </div>
      <div className="p-4 border-t">
        <input 
          type="text" 
          placeholder="Ask about the codebase..."
          className="w-full px-4 py-2 border rounded-lg"
        />
      </div>
    </div>
  )
}
