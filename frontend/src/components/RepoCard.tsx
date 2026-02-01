interface RepoCardProps {
  name: string;
  description: string;
}

export default function RepoCard({ name, description }: RepoCardProps) {
  return (
    <div className="p-4 border rounded-lg hover:shadow-lg transition">
      <h3 className="text-xl font-semibold">{name}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}
