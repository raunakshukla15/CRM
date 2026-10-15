import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { apiError } from '../lib/api.js';
import { money, timeAgo } from '../lib/format.js';
import { Loader, ErrorAlert, EmptyState, StatCard, StatusBadge, Card, linkAction, inputCls, btnPrimary } from '../components/ui.jsx';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');

  async function load(f = {}, t = {}) {
    setLoading(true);
    setError('');
    try {
      const params = {};
      const df = f.from ?? from;
      const dt = t.to ?? to;
      if (df) params.date_from = new Date(df).toISOString();
      if (dt) params.date_to = new Date(dt + 'T23:59:59').toISOString();
      const { data } = await api.get('/dashboard', { params });
      setData(data);
    } catch (e) {
      setError(apiError(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) return <Loader label="Loading dashboard…" />;
  if (error) return <ErrorAlert message={error} onRetry={() => load()} />;
  if (!data) return null;

  const s = data.stats;
  const maxRev = Math.max(1, ...data.orders_by_day.map((d) => d.revenue));
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold">Dashboard</h1>
          <p className="text-xs text-gray-500">Welcome back! Here's what's happening with your store.</p>
        </div>
        <form
          className="flex items-center gap-1.5"
          onSubmit={(e) => { e.preventDefault(); load(); }}
        >
          <input type="date" className={`${inputCls} !w-auto text-xs`} value={from} onChange={(e) => setFrom(e.target.value)} title="From" />
          <input type="date" className={`${inputCls} !w-auto text-xs`} value={to} onChange={(e) => setTo(e.target.value)} title="To" />
          <button type="submit" className={`${btnPrimary} !py-1.5`}>Apply</button>
          {(from || to) && (
            <button type="button" className="text-xs text-gray-500 hover:underline" onClick={() => { setFrom(''); setTo(''); load({ from: '' }, { to: '' }); }}>
              Clear
            </button>
          )}
        </form>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="Customers" value={s.total_customers} sub={`+${s.new_customers} last 30d`} icon="◉" color="blue" />
        <StatCard label="Orders" value={s.total_orders} icon="🛒" color="purple" />
        <StatCard label="Revenue" value={money(s.total_revenue)} icon="💲" color="green" />
        <StatCard label="Completed orders" value={s.completed_orders} icon="✓" color="green" />
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="Pending orders" value={s.pending_orders} icon="◷" color="orange" />
        <StatCard label="VIP customers" value={s.vip_customers} icon="★" color="yellow" />
        <StatCard label="Overdue follow-ups" value={s.overdue_followups} sub="Needs attention" icon="⚠" color="red" />
        <StatCard label="Upcoming follow-ups" value={s.upcoming_followups} icon="📅" color="blue" />
      </div>

      <Card title="Revenue — last 14 days">
        {data.orders_by_day.length === 0 ? (
          <EmptyState title="No orders in range" />
        ) : (
          <div className="flex items-end gap-1 h-28 pt-2">
            {data.orders_by_day.map((d) => (
              <div key={d.date} className="flex-1 flex flex-col items-center gap-1" title={`${d.date}: ${d.orders} orders, ${money(d.revenue)}`}>
                <div
                  className="w-full bg-indigo-500 rounded-t"
                  style={{ height: `${Math.max(4, (d.revenue / maxRev) * 90)}px` }}
                />
                <span className="text-[9px] text-gray-400">{d.date.slice(5)}</span>
              </div>
            ))}
          </div>
        )}
      </Card>

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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Card
          title="Recent customers"
          action={<Link to="/customers" className={linkAction}>View all →</Link>}
        >
          {data.recent_customers.length === 0 ? (
            <EmptyState title="No customers yet" />
          ) : (
            <ul className="divide-y divide-gray-100 text-xs">
              {data.recent_customers.map((c) => (
                <li key={c.id} className="py-2 flex items-center justify-between gap-2">
                  <Link to={`/customers/${c.id}`} className="text-indigo-600 font-medium hover:underline">
                    {c.first_name} {c.last_name}
                  </Link>
                  <span className="text-gray-400">{c.email}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

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
    </div>
  );
}
