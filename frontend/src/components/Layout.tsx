import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Analyze' },
  { to: '/projects', label: 'Projects' },
]

export default function Layout() {
  return (
    <div className="min-h-screen flex">
      <aside className="w-56 border-r border-gray-800 bg-gray-950 p-4 flex flex-col gap-2">
        <h1 className="text-lg font-semibold text-white mb-4">EO Story AI</h1>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `block px-3 py-2 rounded text-sm ${
                isActive
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-900'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
