import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import api, { apiError } from '../lib/api.js';
import { money } from '../lib/format.js';
import { Loader, ErrorAlert, EmptyState, StatusBadge, Card, Avatar, linkAction } from '../components/ui.jsx';
import { FollowUpModal, InteractionForm, NoteForm, CustomerModal } from '../components/forms.jsx';

export default function CustomerDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [followOpen, setFollowOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);

  async function load() {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get(`/customers/${id}`);
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
  }, [id]);

  if (loading) return <Loader label="Loading customer…" />;
  if (error) return <ErrorAlert message={error} onRetry={load} />;
  if (!data) return null;

  const timeline = [
    ...data.interactions.map((i) => ({
      at: i.created_at,
      label: `${i.interaction_type}${i.outcome ? ` · ${i.outcome}` : ''}`,
      text: i.description,
    })),
    ...data.notes.map((n) => ({ at: n.created_at, label: `note by ${n.created_by}`, text: n.note })),
    ...data.communication_logs.map((c) => ({
      at: c.sent_at,
      label: `${c.message_type} · ${c.status}`,
      text: c.payload?.subject || c.recipient_email,
    })),
  ].sort((a, b) => new Date(b.at) - new Date(a.at));

  return (
    <div className="space-y-3">
      <Link to="/customers" className="text-xs text-gray-500 hover:text-indigo-600">
        ← Back to customers
      </Link>

      <Card>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-3">
            <Avatar first={data.first_name} last={data.last_name} />
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-bold">
                  {data.first_name} {data.last_name}
                </h1>
                <StatusBadge value={data.customer_status} />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 mt-1 text-xs text-gray-500">
                <p>✉ {data.email}</p>
                <p>📞 {data.phone || '—'}</p>
                <p>💲 Total spending: {money(data.total_spend)}</p>
                <p>🛒 Orders: {data.lifetime_orders}</p>
                <p>📍 City: {data.billing_address?.city || '—'}</p>
                {data.woocommerce_customer_id && <p>◈ WooCommerce ID: {data.woocommerce_customer_id}</p>}
              </div>
            </div>
          </div>
          <div className="flex gap-2 shrink-0">
            <button
              onClick={() => setEditOpen(true)}
              className="border border-gray-200 rounded-md px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
            >
              ✎ Edit
            </button>
            <button
              onClick={async () => {
                if (!window.confirm(`Delete ${data.first_name} ${data.last_name} and ALL related orders, notes and history?`)) return;
                try {
                  await api.delete(`/customers/${data.id}`);
                  navigate('/customers');
                } catch (e) {
                  setError(apiError(e));
                }
              }}
              className="border border-red-200 rounded-md px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
            >
              Delete
            </button>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Card title={`Order history (${data.orders.length})`}>
          {data.orders.length === 0 ? (
            <EmptyState title="No orders" />
          ) : (
            <ul className="divide-y divide-gray-100 text-xs">
              {data.orders.map((o) => (
                <li key={o.id} className="py-2 flex items-center justify-between gap-2">
                  <span className="text-gray-500">
                    <span className="font-medium text-gray-700">#{o.woocommerce_order_id}</span>{' '}
                    {new Date(o.created_at).toLocaleDateString()}
                  </span>
                  <span className="flex gap-1 items-center">
                    <StatusBadge value={o.status} />
                    <StatusBadge value={o.payment_status} />
                    <span className="font-medium">{money(o.order_total)}</span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card
          title={`Follow-ups (${data.followups.length})`}
          action={<button onClick={() => setFollowOpen(true)} className={linkAction}>+ New follow-up</button>}
        >
          {data.followups.length === 0 ? (
            <EmptyState icon="▭" title="No follow-ups" hint="Create a follow-up to keep track of this customer." />
          ) : (
            <ul className="divide-y divide-gray-100 text-xs">
              {data.followups.map((f) => (
                <li key={f.id} className="py-2">
                  <StatusBadge value={f.status} /> {f.title}
                  <span className="text-gray-400"> — due {new Date(f.due_date).toLocaleString()}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card title="Communication timeline">
        {timeline.length === 0 ? (
          <EmptyState icon="💬" title="No interactions yet" hint="Log the first call, email or meeting below." />
        ) : (
          <ul className="divide-y divide-gray-100 text-xs">
            {timeline.map((t, i) => (
              <li key={i} className="py-2">
                <span className="font-medium">{t.label}</span>{' '}
                <span className="text-gray-400">{new Date(t.at).toLocaleString()}</span>
                <p className="text-gray-600">{t.text}</p>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Card>
          <InteractionForm customerId={data.id} onAdded={load} />
        </Card>
        <Card>
          <NoteForm customerId={data.id} onAdded={load} />
        </Card>
      </div>

      <FollowUpModal
        open={followOpen}
        onClose={() => setFollowOpen(false)}
        customers={[]}
        presetCustomerId={data.id}
        onCreated={load}
      />
      <CustomerModal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        initial={data}
        onSaved={load}
      />
    </div>
  );
}
