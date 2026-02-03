export default function AppFooter() {
  return (
    <footer className="border-t border-white/10 bg-slate-950/70">
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-6 text-sm text-white/60">
        <span>(c) {new Date().getFullYear()} DocuBot</span>
        <div className="flex flex-wrap items-center gap-4">
          <span>Build fast. Document faster.</span>
          <span className="text-white/40">|</span>
          <span className="text-white/50">Powered by Ollama + Groq</span>
        </div>
      </div>
    </footer>
  )
}
