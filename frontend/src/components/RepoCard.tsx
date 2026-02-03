interface RepoCardProps {
  name: string
  description: string
}

export default function RepoCard({ name, description }: RepoCardProps) {
  return (
    <div className="glass rounded-2xl p-4 transition hover:border-emerald-300/40">
      <h3 className="text-lg font-semibold text-white">{name}</h3>
      <p className="mt-1 text-sm text-white/60">{description}</p>
    </div>
  )
}
