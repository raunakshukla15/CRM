import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { apiError } from '../lib/api.js';
import { money, timeAgo } from '../lib/format.js';
import { Loader, ErrorAlert, EmptyState, StatCard, StatusBadge, Card, linkAction } from '../components/ui.jsx';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get('/dashboard');
      setData(data);
    } catch (e) {
      setError(apiError(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) return <Loader label="Loading dashboard…" />;
  if (error) return <ErrorAlert message={error} onRetry={load} />;
  if (!data) return null;

  const s = data.stats;
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Dashboard</h1>
          <p className="text-xs text-gray-500">Welcome back! Here's what's happening with your store.</p>
        </div>
        <button className="bg-white border border-gray-200 rounded-md px-3 py-1.5 text-xs font-medium text-gray-600">
          Today ▾
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        <StatCard label="Customers" value={s.total_customers} icon="◉" color="blue" />
        <StatCard label="Orders" value={s.total_orders} icon="🛒" color="purple" />
        <StatCard label="Revenue" value={money(s.total_revenue)} icon="💲" color="green" />
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="Pending orders" value={s.pending_orders} icon="◷" color="orange" />
        <StatCard label="VIP customers" value={s.vip_customers} icon="★" color="yellow" />
        <StatCard label="Overdue follow-ups" value={s.overdue_followups} sub="Needs attention" icon="⚠" color="red" />
        <StatCard label="Upcoming follow-ups" value={s.upcoming_followups} icon="📅" color="blue" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Card
          title="Recent orders"
          action={<Link to="/orders" className={linkAction}>View all →</Link>}
        >
          {data.recent_orders.length === 0 ? (
            <EmptyState title="No orders yet" hint="Sync the store or wait for webhooks." />
          ) : (
            <ul className="divide-y divide-gray-100 text-xs">
              {data.recent_orders.map((o) => (
                <li key={o.id} className="py-2 flex items-center justify-between gap-2">
                  <span className="text-gray-600">
                    <Link to={`/customers/${o.customer_id}`} className="text-indigo-600 font-medium hover:underline">
                      #{o.woocommerce_order_id}
                    </Link>{' '}
                    {o.customer_email}
                  </span>
                  <span className="flex items-center gap-2 shrink-0">
                    <StatusBadge value={o.status} />
                    <span className="font-medium">{money(o.order_total)}</span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card
          title="Follow-ups needing attention"
          action={<Link to="/followups" className={linkAction}>View all →</Link>}
        >
          {data.overdue_followups.length === 0 && data.upcoming_followups.length === 0 ? (
            <EmptyState title="All caught up" hint="No pending follow-ups." />
          ) : (
            <ul className="divide-y divide-gray-100 text-xs">
              {data.overdue_followups.map((f) => (
                <li key={`o-${f.id}`} className="py-2 flex items-center justify-between gap-2">
                  <span>
                    <StatusBadge value="overdue" /> {f.title}
                    <span className="text-gray-400"> — {f.customer_email}</span>
                  </span>
                  <Link to="/followups" className={linkAction}>View</Link>
                </li>
              ))}
              {data.upcoming_followups.map((f) => (
                <li key={`u-${f.id}`} className="py-2">
                  {f.title}
                  <span className="text-gray-400">
                    {' '}{f.customer_email} · due {new Date(f.due_date).toLocaleDateString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card title="Recent activity">
        {data.recent_activity.length === 0 ? (
          <EmptyState title="No activity yet" />
        ) : (
          <ul className="divide-y divide-gray-100 text-xs">
            {data.recent_activity.map((a) => (
              <li key={`${a.kind}-${a.id}`} className="py-2 flex items-center justify-between gap-2">
                <span className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-indigo-50 text-indigo-500 flex items-center justify-center">✉</span>
                  {a.text}{' '}
                  <Link to={`/customers/${a.customer_id}`} className="text-indigo-600 hover:underline">
                    #{a.customer_id}
                  </Link>
                </span>
                <span className="text-gray-400 shrink-0">{timeAgo(a.at)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
