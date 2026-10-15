import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api, { apiError } from '../lib/api.js';
import { money } from '../lib/format.js';
import { Loader, ErrorAlert, EmptyState, StatusBadge, Card, inputCls, btnPrimary } from '../components/ui.jsx';
import { CustomerModal } from '../components/forms.jsx';

export default function Customers() {
  const [params, setParams] = useSearchParams();
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState(params.get('q') || '');
  const [status, setStatus] = useState('');
  const [orderStatus, setOrderStatus] = useState('');
  const [sort, setSort] = useState('newest');
  const [modalOpen, setModalOpen] = useState(false);

  async function load(over = {}) {
    setLoading(true);
    setError('');
    try {
      const p = {
        page: 1,
        page_size: 50,
        search: over.search ?? search,
        status: over.status ?? status,
        order_status: over.order_status ?? orderStatus,
        sort: over.sort ?? sort,
      };
      Object.keys(p).forEach((k) => !p[k] && delete p[k]);
      const { data } = await api.get('/customers', { params: p });
      setItems(data.items);
      setTotal(data.total);
    } catch (e) {
      setError(apiError(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const q = params.get('q') || '';
    setSearch(q);
    load({ search: q });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  async function remove(c) {
    if (!window.confirm(`Delete ${c.first_name} ${c.last_name} and ALL of their orders, notes and history?`)) return;
    try {
      await api.delete(`/customers/${c.id}`);
      load();
    } catch (e) {
      setError(apiError(e));
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold">Customers ({total})</h1>
          <p className="text-xs text-gray-500">Manage your customers and their information.</p>
        </div>
        <button className={btnPrimary} onClick={() => setModalOpen(true)}>
          + Add customer
        </button>
      </div>

      <form
        className="grid grid-cols-2 sm:grid-cols-5 gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          setParams(search ? { q: search } : {});
          load();
        }}
      >
        <input
          className={inputCls}
          placeholder="Search name, email, phone…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className={inputCls} value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="Lead">Lead</option>
          <option value="Active">Active</option>
          <option value="VIP">VIP</option>
          <option value="Churned">Churned</option>
        </select>
        <select
          className={inputCls}
          value={orderStatus}
          onChange={(e) => setOrderStatus(e.target.value)}
        >
          <option value="">Any order status</option>
          <option value="pending">Pending</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
        </select>
        <select className={inputCls} value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="newest">Newest first</option>
          <option value="spend">Highest spend</option>
          <option value="name">Name A–Z</option>
        </select>
        <button type="submit" className={btnPrimary}>
          Search
        </button>
      </form>

      {error && <ErrorAlert message={error} onRetry={() => load()} />}
      {loading ? (
        <Loader label="Loading customers…" />
      ) : items.length === 0 ? (
        <Card>
          <EmptyState title="No customers found" hint="Adjust filters or add your first customer." />
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto -m-4 p-4">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="py-2 pr-4 font-medium">Customer</th>
                  <th className="py-2 pr-4 font-medium">Email</th>
                  <th className="py-2 pr-4 font-medium">Status</th>
                  <th className="py-2 pr-4 font-medium">Spend</th>
                  <th className="py-2 pr-4 font-medium">Orders</th>
                  <th className="py-2 font-medium" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((c) => (
                  <tr key={c.id}>
                    <td className="py-2.5 pr-4">
                      <Link to={`/customers/${c.id}`} className="text-indigo-600 hover:underline font-medium">
                        {c.first_name} {c.last_name}
                      </Link>
                    </td>
                    <td className="py-2.5 pr-4 text-gray-500">{c.email}</td>
                    <td className="py-2.5 pr-4">
                      <StatusBadge value={c.customer_status} />
                    </td>
                    <td className="py-2.5 pr-4 font-medium">{money(c.total_spend)}</td>
                    <td className="py-2.5 pr-4">{c.lifetime_orders}</td>
                    <td className="py-2.5">
                      <button onClick={() => remove(c)} className="text-red-500 hover:underline">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <CustomerModal open={modalOpen} onClose={() => setModalOpen(false)} onSaved={() => load()} />
    </div>
  );
}
