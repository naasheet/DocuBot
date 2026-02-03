import Link from 'next/link'
import AuthHomeRedirect from '../components/AuthHomeRedirect'

const features = [
  {
    title: 'Auto README',
    description: 'Generate and keep README files current using real repo structure.',
  },
  {
    title: 'API Docs',
    description: 'Extract signatures and docstrings into clean markdown docs.',
  },
  {
    title: 'Code Chat',
    description: 'Ask questions across your repo with RAG-powered context.',
  },
  {
    title: 'Webhook Refresh',
    description: 'Re-index only changed files for fast incremental updates.',
  },
]

const quickLinks = [
  { label: 'Open Dashboard', href: '/dashboard' },
  { label: 'Browse Repos', href: '/repos' },
  { label: 'Docs Viewer', href: '/docs' },
  { label: 'Ask the Code', href: '/chat' },
]

export default function Home() {
  return (
    <main className="text-white">
      <AuthHomeRedirect />
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 opacity-60">
          <div className="absolute left-[-10%] top-[-20%] h-96 w-96 rounded-full bg-emerald-400/20 blur-3xl" />
          <div className="absolute right-[-10%] top-[10%] h-[28rem] w-[28rem] rounded-full bg-sky-400/20 blur-3xl" />
        </div>
        <div className="relative mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-20 md:py-28">
          <div className="flex flex-col gap-6 md:max-w-3xl">
            <p className="text-sm uppercase tracking-[0.3em] text-white/60">
              AI Documentation Ops
            </p>
            <h1 className="font-display text-4xl font-semibold leading-tight md:text-6xl">
              DocuBot turns repos into living documentation.
            </h1>
            <p className="text-lg text-white/70 md:text-xl">
              Analyze code locally, generate README and API docs, and let teams ask
              questions with accurate context. All without paid APIs.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link
                href="/register"
                className="rounded-full bg-emerald-300 px-6 py-3 text-sm font-semibold text-slate-900 transition hover:-translate-y-0.5 hover:bg-emerald-200"
              >
                Start documenting
              </Link>
              <Link
                href="/login"
                className="rounded-full border border-white/20 px-6 py-3 text-sm font-semibold text-white/80 transition hover:border-white/60 hover:text-white"
              >
                Sign in
              </Link>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {features.map((feature) => (
              <div key={feature.title} className="glass rounded-2xl p-6">
                <h3 className="text-lg font-semibold">{feature.title}</h3>
                <p className="mt-2 text-sm text-white/70">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-16 md:flex-row md:items-start">
        <div className="glass flex-1 rounded-2xl p-6">
          <h2 className="font-display text-2xl">How it works</h2>
          <ol className="mt-4 space-y-4 text-sm text-white/70">
            <li>
              <span className="text-white">1.</span> Add a GitHub repo and pull a fast tree for UI.
            </li>
            <li>
              <span className="text-white">2.</span> Worker clones and parses code for deep analysis.
            </li>
            <li>
              <span className="text-white">3.</span> Generate docs + embeddings for search and chat.
            </li>
          </ol>
        </div>

        <div className="glass flex-1 rounded-2xl p-6">
          <h2 className="font-display text-2xl">Quick access</h2>
          <div className="mt-4 grid gap-3">
            {quickLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/80 transition hover:border-white/30 hover:text-white"
              >
                <span>{link.label}</span>
                <span className="text-white/40">-&gt;</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-6 pb-20">
        <div className="glass rounded-2xl p-8 text-center">
          <h2 className="font-display text-3xl">Ready to ship better docs?</h2>
          <p className="mt-3 text-sm text-white/70">
            Connect a repository and let DocuBot keep README and API docs in sync.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-4">
            <Link
              href="/register"
              className="rounded-full bg-white px-6 py-3 text-sm font-semibold text-slate-900 transition hover:-translate-y-0.5 hover:bg-white/90"
            >
              Create account
            </Link>
            <Link
              href="/repos"
              className="rounded-full border border-white/20 px-6 py-3 text-sm font-semibold text-white/80 transition hover:border-white/60 hover:text-white"
            >
              Browse repos
            </Link>
          </div>
        </div>
      </section>
    </main>
  )
}
