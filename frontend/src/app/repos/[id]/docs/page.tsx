export default function DocsPage({ params }: { params: { id: string } }) {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">Documentation</h1>
      <p>Documentation for repository {params.id} will appear here.</p>
    </div>
  )
}
