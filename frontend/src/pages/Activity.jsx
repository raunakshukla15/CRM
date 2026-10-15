import { useEffect, useState } from 'react';
import api, { apiError } from '../lib/api.js';
import { Loader, ErrorAlert, EmptyState, Card, inputCls, btnPrimary } from '../components/ui.jsx';

const ACTIONS = [
  '', 'account.registered', 'auth.login', 'auth.login_failed', 'auth.logout',
  'auth.password_changed', 'auth.password_reset', 'auth.reset_requested',
  'account.deleted', 'customer.created', 'customer.updated', 'customer.deleted',
  'order.created', 'order.status_changed', 'order.deleted',
  'communication.created', 'communication.updated', 'communication.deleted',
  'followup.created', 'followup.updated', 'followup.deleted',
];

export default function Activity() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [action, setAction] = useState('');
  const [entityType, setEntityType] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const params = { page: 1, page_size: 50 };
      if (action) params.action = action;
      if (entityType) params.entity_type = entityType;
      const { data } = await api.get('/activity', { params });
      setItems(data.items);
      setTotal(data.total);
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

  return (
    <div className="space-y-3">
      <div>
        <h1 className="text-xl font-bold">Activity history ({total})</h1>
        <p className="text-xs text-gray-500">Audit trail of your account and CRM events. Written by the backend — read-only.</p>
      </div>

      <form className="grid grid-cols-1 sm:grid-cols-3 gap-2" onSubmit={(e) => { e.preventDefault(); load(); }}>
        <select className={inputCls} value={action} onChange={(e) => setAction(e.target.value)}>
          <option value="">All actions</option>
          {ACTIONS.filter(Boolean).map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
        <select className={inputCls} value={entityType} onChange={(e) => setEntityType(e.target.value)}>
          <option value="">All record types</option>
          <option value="user">User</option>
          <option value="customer">Customer</option>
          <option value="order">Order</option>
          <option value="interaction">Communication</option>
          <option value="followup">Follow-up</option>
        </select>
        <button type="submit" className={btnPrimary}>Filter</button>
      </form>

      {error && <ErrorAlert message={error} onRetry={load} />}
      {loading ? <Loader label="Loading activity…" /> : items.length === 0 ? (
        <Card><EmptyState title="No activity yet" /></Card>
      ) : (
        <Card>
          <ul className="divide-y divide-gray-100 text-xs">
            {items.map((a) => (
              <li key={a.id} className="py-2 flex items-center justify-between gap-2">
                <div>
                  <span className="font-mono bg-gray-100 rounded px-1.5 py-0.5">{a.action}</span>{' '}
                  <span className="text-gray-600">{a.description}</span>
                  {a.entity_type && <span className="text-gray-400"> · {a.entity_type}{a.entity_id ? ` #${a.entity_id}` : ''}</span>}
                </div>
                <span className="text-gray-400 shrink-0">{new Date(a.created_at).toLocaleString()}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
