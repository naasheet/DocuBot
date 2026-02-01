export default function RepoDetailPage({ params }: { params: { id: string } }) {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">Repository {params.id}</h1>
      <p>Repository details will appear here.</p>
    </div>
  )
}
