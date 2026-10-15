import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { apiError } from '../lib/api.js';
import { money } from '../lib/format.js';
import { Loader, ErrorAlert, EmptyState, StatusBadge, Card, inputCls, btnPrimary } from '../components/ui.jsx';

export default function Orders() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');

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
        <h1 className="text-xl font-bold">Orders ({total})</h1>
        <p className="text-xs text-gray-500">View and manage all WooCommerce orders.</p>
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
          <option value="pending">Pending</option>
          <option value="processing">Processing</option>
          <option value="on-hold">On hold</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
          <option value="refunded">Refunded</option>
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
                  <th className="py-2 pr-4 font-medium">Order</th>
                  <th className="py-2 pr-4 font-medium">Customer</th>
                  <th className="py-2 pr-4 font-medium">Status</th>
                  <th className="py-2 pr-4 font-medium">Payment</th>
                  <th className="py-2 pr-4 font-medium">Fulfillment</th>
                  <th className="py-2 font-medium">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((o) => (
                  <tr key={o.id}>
                    <td className="py-2.5 pr-4 font-medium">#{o.woocommerce_order_id}</td>
                    <td className="py-2.5 pr-4">
                      <Link to={`/customers/${o.customer_id}`} className="text-indigo-600 hover:underline">
                        Customer #{o.customer_id}
                      </Link>
                    </td>
                    <td className="py-2.5 pr-4">
                      <StatusBadge value={o.status} />
                    </td>
                    <td className="py-2.5 pr-4">
                      <StatusBadge value={o.payment_status} />
                    </td>
                    <td className="py-2.5 pr-4">
                      <StatusBadge value={o.fulfillment_status} />
                    </td>
                    <td className="py-2.5 font-medium">{money(o.order_total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
