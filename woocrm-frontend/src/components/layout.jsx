import { useEffect, useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import api from '../lib/api.js';

const NAV = [
  { to: '/', label: 'Dashboard', icon: '▦', end: true },
  { to: '/customers', label: 'Customers', icon: '◉' },
  { to: '/orders', label: 'Orders', icon: '▤' },
  { to: '/followups', label: 'Follow-ups', icon: '◔' },
  { to: '/integrations', label: 'Integrations', icon: '⛭' },
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
  return (
    <aside className="w-48 shrink-0 bg-white border-r min-h-screen hidden md:flex md:flex-col sticky top-0 h-screen">
      <Logo />
      <nav className="px-3 space-y-1">
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
  const [q, setQ] = useState('');
  const [overdue, setOverdue] = useState(0);

  useEffect(() => {
    api
      .get('/followups', { params: { status: 'overdue', page: 1, page_size: 1 } })
      .then(({ data }) => setOverdue(data.total || 0))
      .catch(() => {});
  }, []);

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
      <span className="w-8 h-8 rounded-full bg-indigo-400 text-white flex items-center justify-center text-sm font-medium">
        R
      </span>
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
