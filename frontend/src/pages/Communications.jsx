import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { apiError } from '../lib/api.js';
import { Loader, ErrorAlert, EmptyState, StatusBadge, Card, inputCls, btnPrimary } from '../components/ui.jsx';

const TYPES = ['call', 'email', 'meeting', 'note'];

export default function Communications() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [customers, setCustomers] = useState([]);
  const [filters, setFilters] = useState({ customer_id: '', interaction_type: '', status: '', search: '' });
  const [form, setForm] = useState({ customer_id: '', interaction_type: 'call', subject: '', description: '', outcome: '', scheduled_at: '' });
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setError('');
    try {
      const params = { page: 1, page_size: 50 };
      Object.entries(filters).forEach(([k, v]) => v && (params[k] = v));
      const { data } = await api.get('/interactions', { params });
      setItems(data.items);
      setTotal(data.total);
      const c = await api.get('/customers', { params: { page: 1, page_size: 100 } });
      setCustomers(c.data.items);
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

  async function create(e) {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const payload = {
        customer_id: Number(form.customer_id),
        interaction_type: form.interaction_type,
        subject: form.subject || null,
        description: form.description,
        outcome: form.outcome || null,
        scheduled_at: form.scheduled_at ? new Date(form.scheduled_at).toISOString() : null,
      };
      await api.post('/interactions', payload);
      setSuccess('Communication recorded.');
      setForm({ customer_id: '', interaction_type: 'call', subject: '', description: '', outcome: '', scheduled_at: '' });
      load();
    } catch (e) {
      setError(apiError(e));
    } finally {
      setSaving(false);
    }
  }

  async function markComplete(item) {
    try {
      await api.patch(`/interactions/${item.id}`, {
        status: 'completed',
        completed_at: new Date().toISOString(),
      });
      load();
    } catch (e) {
      setError(apiError(e));
    }
  }

  async function remove(item) {
    if (!window.confirm(`Delete this ${item.interaction_type} record?`)) return;
    try {
      await api.delete(`/interactions/${item.id}`);
      load();
    } catch (e) {
      setError(apiError(e));
    }
  }

  const setF = (k) => (e) => setFilters({ ...filters, [k]: e.target.value });

  return (
    <div className="space-y-3">
      <div>
        <h1 className="text-xl font-bold">Communications ({total})</h1>
        <p className="text-xs text-gray-500">Log calls, emails and meetings. Manual records only — nothing is auto-sent.</p>
      </div>

      {error && <ErrorAlert message={error} onRetry={load} />}
      {success && <div className="rounded-md bg-green-50 border border-green-200 p-3 text-xs text-green-700">{success}</div>}

      <Card title="Log a communication">
        <form onSubmit={create} className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <select className={inputCls} value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })} required>
            <option value="">Select customer…</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>{c.first_name} {c.last_name} — {c.email}</option>
            ))}
          </select>
          <select className={inputCls} value={form.interaction_type} onChange={(e) => setForm({ ...form, interaction_type: e.target.value })}>
            {TYPES.map((t) => <option key={t} value={t}>{t[0].toUpperCase() + t.slice(1)}</option>)}
          </select>
          <input className={inputCls} placeholder="Subject (optional)" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} />
          <input className={inputCls} placeholder="Outcome (optional)" value={form.outcome} onChange={(e) => setForm({ ...form, outcome: e.target.value })} />
          <textarea className={`${inputCls} sm:col-span-2`} rows={3} placeholder="Summary of what was discussed…" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
          <input type="datetime-local" className={inputCls} title="Scheduled time (optional)" value={form.scheduled_at} onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })} />
          <button type="submit" className={btnPrimary} disabled={saving}>{saving ? 'Saving…' : 'Log communication'}</button>
        </form>
      </Card>

      <form
        className="grid grid-cols-2 sm:grid-cols-5 gap-2"
        onSubmit={(e) => { e.preventDefault(); load(); }}
      >
        <select className={inputCls} value={filters.customer_id} onChange={setF('customer_id')}>
          <option value="">All customers</option>
          {customers.map((c) => (
            <option key={c.id} value={c.id}>{c.email}</option>
          ))}
        </select>
        <select className={inputCls} value={filters.interaction_type} onChange={setF('interaction_type')}>
          <option value="">All types</option>
          {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select className={inputCls} value={filters.status} onChange={setF('status')}>
          <option value="">Any status</option>
          <option value="logged">Logged</option>
          <option value="completed">Completed</option>
        </select>
        <input className={inputCls} placeholder="Search…" value={filters.search} onChange={setF('search')} />
        <button type="submit" className={btnPrimary}>Filter</button>
      </form>

      {loading ? <Loader label="Loading communications…" /> : items.length === 0 ? (
        <Card><EmptyState title="No communications" hint="Log your first call, email or meeting above." /></Card>
      ) : (
        <div className="space-y-2">
          {items.map((i) => (
            <Card key={i.id}>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="text-xs">
                  <p className="font-medium text-sm">
                    {i.interaction_type} <StatusBadge value={i.status} />
                    {i.subject && <span className="text-gray-700"> — {i.subject}</span>}
                  </p>
                  <p className="text-indigo-600 mt-0.5">
                    <Link to={`/customers/${i.customer_id}`} className="hover:underline">
                      {i.customer_email || `Customer #${i.customer_id}`}
                    </Link>
                    <span className="text-gray-400"> · {new Date(i.created_at).toLocaleString()}</span>
                  </p>
                  <p className="text-gray-600 mt-1">{i.description}</p>
                  {i.outcome && <p className="text-gray-400 mt-0.5">Outcome: {i.outcome}</p>}
                </div>
                <div className="flex gap-2">
                  {i.status !== 'completed' && (
                    <button onClick={() => markComplete(i)} className="text-xs px-3 py-1.5 rounded-md bg-green-600 text-white hover:bg-green-700 whitespace-nowrap">
                      Mark completed
                    </button>
                  )}
                  <button onClick={() => remove(i)} className="text-xs px-3 py-1.5 rounded-md border border-gray-200 text-red-600 hover:bg-red-50 whitespace-nowrap">
                    Delete
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
