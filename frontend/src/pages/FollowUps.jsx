import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { apiError } from '../lib/api.js';
import { Loader, ErrorAlert, EmptyState, StatusBadge, Card, btnPrimary } from '../components/ui.jsx';
import { FollowUpModal } from '../components/forms.jsx';

const TABS = ['all', 'pending', 'overdue', 'upcoming', 'completed', 'cancelled'];

export default function FollowUps() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [filter, setFilter] = useState('all');
  const [modalOpen, setModalOpen] = useState(false);
  const [customers, setCustomers] = useState([]);

  async function load(f = filter) {
    setLoading(true);
    setError('');
    try {
      const params = { page: 1, page_size: 50 };
      if (f !== 'all') params.status = f;
      const { data } = await api.get('/followups', { params });
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

  async function setStatus(f, status) {
    setError('');
    setSuccess('');
    try {
      await api.patch(`/followups/${f.id}`, { status });
      setSuccess(`Follow-up "${f.title}" marked as ${status}.`);
      load();
    } catch (e) {
      setError(apiError(e));
    }
  }

  useEffect(() => {
    load(filter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold">Follow-ups ({total})</h1>
          <p className="text-xs text-gray-500">Track and manage customer follow-ups.</p>
        </div>
        <button className={btnPrimary} onClick={() => setModalOpen(true)}>
          + Create follow-up
        </button>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {TABS.map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium ${
              filter === s ? 'bg-indigo-600 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            {s[0].toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {error && <ErrorAlert message={error} onRetry={() => load()} />}
      {success && (
        <div className="rounded-md bg-green-50 border border-green-200 p-3 text-xs text-green-700">
          {success}
        </div>
      )}

      {loading ? (
        <Loader label="Loading follow-ups…" />
      ) : items.length === 0 ? (
        <Card>
          <EmptyState title="No follow-ups" hint="Create one to remind yourself to call a customer." />
        </Card>
      ) : (
        <div className="space-y-2">
          {items.map((f) => (
            <Card key={f.id}>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="text-xs">
                  <p className="font-medium text-sm">
                    {f.title} <StatusBadge value={f.status} />{' '}
                    {f.is_overdue && <StatusBadge value="overdue" />}
                  </p>
                  <p className="text-indigo-600 mt-0.5">
                    <Link to={`/customers/${f.customer_id}`} className="hover:underline">
                      {f.customer_email || `Customer #${f.customer_id}`}
                    </Link>
                    <span className="text-gray-400">
                      {' '}· due {new Date(f.due_date).toLocaleString()}
                    </span>
                  </p>
                  {f.notes && <p className="text-gray-500 mt-1">{f.notes}</p>}
                </div>
                {f.status === 'pending' ? (
                  <button
                    onClick={() => setStatus(f, 'completed')}
                    className="text-xs px-3 py-1.5 rounded-md bg-green-600 text-white hover:bg-green-700 whitespace-nowrap"
                  >
                    Mark completed
                  </button>
                ) : (
                  f.status === 'completed' && (
                    <button
                      onClick={() => setStatus(f, 'pending')}
                      className="text-xs px-3 py-1.5 rounded-md border border-gray-200 hover:bg-gray-50 whitespace-nowrap"
                    >
                      Reopen
                    </button>
                  )
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      <FollowUpModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        customers={customers}
        onCreated={() => load()}
      />
    </div>
  );
}
