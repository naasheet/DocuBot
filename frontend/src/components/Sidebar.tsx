export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-100 p-4">
      <nav>
        <ul className="space-y-2">
          <li><a href="/dashboard" className="block p-2 hover:bg-gray-200 rounded">Dashboard</a></li>
          <li><a href="/repos" className="block p-2 hover:bg-gray-200 rounded">Repositories</a></li>
          <li><a href="/settings" className="block p-2 hover:bg-gray-200 rounded">Settings</a></li>
        </ul>
      </nav>
    </aside>
  )
}
