import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { apiError } from '../lib/api.js';
import { money } from '../lib/format.js';
import { Loader, ErrorAlert, EmptyState, StatusBadge, Card, Modal, inputCls, btnPrimary, btnGhost } from '../components/ui.jsx';

const STATUSES = ['pending', 'processing', 'on-hold', 'completed', 'cancelled', 'refunded'];

function OrderModal({ open, onClose, customers, onCreated }) {
  const [form, setForm] = useState({ customer_id: '', status: 'pending', total: '', items: [{ name: '', quantity: 1, price: '' }] });
  const [useItems, setUseItems] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  function setItem(i, k, v) {
    const items = form.items.map((it, j) => (j === i ? { ...it, [k]: v } : it));
    setForm({ ...form, items });
  }

  const previewTotal = form.items.reduce((s, it) => s + (Number(it.quantity) || 0) * (Number(it.price) || 0), 0);

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload = { customer_id: Number(form.customer_id), status: form.status };
      if (useItems) {
        payload.line_items = form.items
          .filter((it) => it.name && Number(it.quantity) > 0 && it.price !== '')
          .map((it) => ({ name: it.name, quantity: Number(it.quantity), price: String(it.price) }));
        if (!payload.line_items.length) throw new Error('Add at least one line item.');
      } else {
        payload.total = String(form.total);
      }
      await api.post('/orders', payload);
      onCreated?.();
      onClose();
    } catch (err) {
      setError(err.message || apiError(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open={open} title="Create order" onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        {error && <p className="text-sm text-red-600">{error}</p>}
        <select className={inputCls} value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })} required>
          <option value="">Select customer…</option>
          {customers.map((c) => (
            <option key={c.id} value={c.id}>{c.first_name} {c.last_name} — {c.email}</option>
          ))}
        </select>
        <select className={inputCls} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input type="checkbox" checked={useItems} onChange={(e) => setUseItems(e.target.checked)} />
          Build total from line items (calculated on the backend)
        </label>
        {useItems ? (
          <div className="space-y-2">
            {form.items.map((it, i) => (
              <div key={i} className="grid grid-cols-5 gap-1">
                <input className={`${inputCls} col-span-2`} placeholder="Item name" value={it.name} onChange={(e) => setItem(i, 'name', e.target.value)} />
                <input className={inputCls} type="number" min="1" placeholder="Qty" value={it.quantity} onChange={(e) => setItem(i, 'quantity', e.target.value)} />
                <input className={inputCls} type="number" min="0" step="0.01" placeholder="Price" value={it.price} onChange={(e) => setItem(i, 'price', e.target.value)} />
                <button type="button" className="text-red-500 text-sm" onClick={() => setForm({ ...form, items: form.items.filter((_, j) => j !== i) })}>✕</button>
              </div>
            ))}
            <button type="button" className="text-xs text-indigo-600 hover:underline" onClick={() => setForm({ ...form, items: [...form.items, { name: '', quantity: 1, price: '' }] })}>
              + Add item
            </button>
            <p className="text-xs text-gray-500">Estimated total: {money(previewTotal)}</p>
          </div>
        ) : (
          <input className={inputCls} type="number" min="0" step="0.01" placeholder="Order total" value={form.total} onChange={(e) => setForm({ ...form, total: e.target.value })} required />
        )}
        <div className="flex justify-end gap-2">
          <button type="button" className={btnGhost} onClick={onClose}>Cancel</button>
          <button type="submit" className={btnPrimary} disabled={saving}>{saving ? 'Saving…' : 'Create'}</button>
        </div>
      </form>
    </Modal>
  );
}

export default function Orders() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [expanded, setExpanded] = useState({});
  const [details, setDetails] = useState({});

  async function load() {
    setLoading(true);
    setError('');
    try {
      const params = { page: 1, page_size: 50 };
      if (status) params.status = status;
      if (search) params.search = search;
      const { data } = await api.get('/orders', { params });
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

  async function toggleExpand(o) {
    if (expanded[o.id]) {
      setExpanded({ ...expanded, [o.id]: false });
      return;
    }
    try {
      const { data } = await api.get(`/orders/${o.id}`);
      setDetails({ ...details, [o.id]: data });
      setExpanded({ ...expanded, [o.id]: true });
    } catch (e) {
      setError(apiError(e));
    }
  }

  async function changeStatus(o, newStatus) {
    try {
      await api.patch(`/orders/${o.id}`, { status: newStatus });
      load();
    } catch (e) {
      setError(apiError(e));
    }
  }

  async function remove(o) {
    if (!window.confirm(`Delete order #${o.woocommerce_order_id}? Customer totals will be recalculated.`)) return;
    try {
      await api.delete(`/orders/${o.id}`);
      load();
    } catch (e) {
      setError(apiError(e));
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold">Orders ({total})</h1>
          <p className="text-xs text-gray-500">View and manage all WooCommerce orders.</p>
        </div>
        <button className={btnPrimary} onClick={() => setModalOpen(true)}>+ New order</button>
      </div>
      <form
        className="grid grid-cols-1 sm:grid-cols-3 gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          load();
        }}
      >
        <select className={inputCls} value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <input
          className={inputCls}
          placeholder="Search WooCommerce order ID…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="submit" className={btnPrimary}>
          Filter
        </button>
      </form>

      {error && <ErrorAlert message={error} onRetry={load} />}
      {loading ? (
        <Loader label="Loading orders…" />
      ) : items.length === 0 ? (
        <Card>
          <EmptyState title="No orders found" hint="Adjust filters or sync the store." />
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto -m-4 p-4">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="py-2 pr-2 font-medium" />
                  <th className="py-2 pr-4 font-medium">Order</th>
                  <th className="py-2 pr-4 font-medium">Customer</th>
                  <th className="py-2 pr-4 font-medium">Status</th>
                  <th className="py-2 pr-4 font-medium">Payment</th>
                  <th className="py-2 pr-4 font-medium">Fulfillment</th>
                  <th className="py-2 pr-4 font-medium">Total</th>
                  <th className="py-2 font-medium" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((o) => (
                  <>
                    <tr key={o.id}>
                      <td className="py-2.5 pr-2">
                        <button onClick={() => toggleExpand(o)} className="text-gray-400 hover:text-indigo-600">
                          {expanded[o.id] ? '▾' : '▸'}
                        </button>
                      </td>
                      <td className="py-2.5 pr-4 font-medium">#{o.woocommerce_order_id}</td>
                      <td className="py-2.5 pr-4">
                        <Link to={`/customers/${o.customer_id}`} className="text-indigo-600 hover:underline">
                          Customer #{o.customer_id}
                        </Link>
                      </td>
                      <td className="py-2.5 pr-4">
                        <select
                          className="border border-gray-200 rounded px-1 py-0.5 text-xs bg-white"
                          value={o.status}
                          onChange={(e) => changeStatus(o, e.target.value)}
                        >
                          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                        </select>
                      </td>
                      <td className="py-2.5 pr-4">
                        <StatusBadge value={o.payment_status} />
                      </td>
                      <td className="py-2.5 pr-4">
                        <StatusBadge value={o.fulfillment_status} />
                      </td>
                      <td className="py-2.5 pr-4 font-medium">{money(o.order_total)}</td>
                      <td className="py-2.5">
                        <button onClick={() => remove(o)} className="text-red-500 hover:underline">Delete</button>
                      </td>
                    </tr>
                    {expanded[o.id] && details[o.id] && (
                      <tr key={`${o.id}-x`} className="bg-gray-50">
                        <td colSpan={8} className="py-2 px-4">
                          <p className="font-medium mb-1">Line items</p>
                          {details[o.id].line_items?.length ? (
                            <ul className="list-disc ml-5">
                              {details[o.id].line_items.map((li, i) => (
                                <li key={i}>{li.name} × {li.quantity} — {money(Number(li.price) * Number(li.quantity))}</li>
                              ))}
                            </ul>
                          ) : <p className="text-gray-400">No line items recorded.</p>}
                          <p className="font-medium mt-2 mb-1">Status history</p>
                          {details[o.id].status_history?.length ? (
                            <ul className="list-disc ml-5">
                              {details[o.id].status_history.map((h) => (
                                <li key={h.id}>{h.old_status || '—'} → {h.new_status} <span className="text-gray-400">({new Date(h.created_at).toLocaleString()})</span></li>
                              ))}
                            </ul>
                          ) : <p className="text-gray-400">No history.</p>}
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <OrderModal open={modalOpen} onClose={() => setModalOpen(false)} customers={customers} onCreated={load} />
    </div>
  );
}
