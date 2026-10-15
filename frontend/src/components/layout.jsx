import { useEffect, useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import api from '../lib/api.js';
import { useAuth } from '../lib/auth.jsx';

const NAV = [
  { to: '/', label: 'Dashboard', icon: '▦', end: true },
  { to: '/customers', label: 'Customers', icon: '◉' },
  { to: '/orders', label: 'Orders', icon: '▤' },
  { to: '/communications', label: 'Communications', icon: '✉' },
  { to: '/followups', label: 'Follow-ups', icon: '◔' },
  { to: '/activity', label: 'Activity', icon: '📜' },
  { to: '/settings', label: 'Settings', icon: '⚙' },
];

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 px-2 py-4">
      <span className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold">
        K
      </span>
      <span className="font-bold text-indigo-700">KilloKart</span>
    </Link>
  );
}

function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate('/signin');
  }

  return (
    <aside className="w-52 shrink-0 bg-white border-r min-h-screen hidden md:flex md:flex-col sticky top-0 h-screen">
      <Logo />
      <nav className="px-3 space-y-1 flex-1">
        {NAV.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.end}
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium ${
                isActive ? 'bg-indigo-50 text-indigo-700' : 'text-gray-600 hover:bg-gray-50'
              }`
            }
          >
            <span className="w-4 text-center">{n.icon}</span>
            {n.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-3 border-t">
        <p className="text-xs font-medium text-gray-700 truncate">{user?.full_name}</p>
        <p className="text-[11px] text-gray-400 truncate">{user?.email}</p>
        <button onClick={handleLogout} className="mt-1 text-xs text-indigo-600 hover:underline">
          Log out
        </button>
      </div>
    </aside>
  );
}

function MobileNav() {
  return (
    <nav className="md:hidden bg-white border-b px-2 py-2 flex gap-1 overflow-x-auto sticky top-0 z-10">
      {NAV.map((n) => (
        <NavLink
          key={n.to}
          to={n.to}
          end={n.end}
          className={({ isActive }) =>
            `px-3 py-1.5 rounded-md text-sm font-medium whitespace-nowrap ${
              isActive ? 'bg-indigo-600 text-white' : 'text-gray-700 bg-gray-100'
            }`
          }
        >
          {n.label}
        </NavLink>
      ))}
    </nav>
  );
}

function Topbar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [q, setQ] = useState('');
  const [overdue, setOverdue] = useState(0);
  const [menu, setMenu] = useState(false);

  useEffect(() => {
    api
      .get('/followups', { params: { status: 'overdue', page: 1, page_size: 1 } })
      .then(({ data }) => setOverdue(data.total || 0))
      .catch(() => {});
  }, []);

  const initial = (user?.full_name || 'U').trim()[0]?.toUpperCase() || 'U';

  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <form
        className="flex-1 max-w-md"
        onSubmit={(e) => {
          e.preventDefault();
          navigate(`/customers?q=${encodeURIComponent(q)}`);
        }}
      >
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search customers, orders…"
          className="w-full bg-white border rounded-full px-4 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </form>
      <div className="flex-1" />
      <Link to="/followups" className="relative text-gray-500 hover:text-gray-800" title="Notifications">
        <span className="text-lg">🔔</span>
        {overdue > 0 && (
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full" />
        )}
      </Link>
      <div className="relative">
        <button
          onClick={() => setMenu(!menu)}
          className="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center text-sm font-medium"
          title={user?.email}
        >
          {initial}
        </button>
        {menu && (
          <div className="absolute right-0 mt-1 w-44 bg-white border rounded-lg shadow-lg py-1 text-sm z-20">
            <div className="px-3 py-2 border-b">
              <p className="font-medium truncate">{user?.full_name}</p>
              <p className="text-xs text-gray-400 truncate">{user?.email}</p>
            </div>
            <Link to="/settings" onClick={() => setMenu(false)} className="block px-3 py-2 hover:bg-gray-50">
              Account settings
            </Link>
            <button
              onClick={async () => {
                await logout();
                navigate('/signin');
              }}
              className="block w-full text-left px-3 py-2 hover:bg-gray-50 text-red-600"
            >
              Log out
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Shell({ children }) {
  return (
    <div className="min-h-screen bg-gray-100 flex">
      <Sidebar />
      <div className="flex-1 min-w-0">
        <MobileNav />
        <Topbar />
        <main className="px-4 pb-8 max-w-6xl">{children}</main>
      </div>
    </div>
  );
}
