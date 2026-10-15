import { useEffect, useState } from 'react';
import api, { apiError } from '../lib/api.js';
import { Loader, ErrorAlert, EmptyState, Card, btnPrimary, StatusBadge } from '../components/ui.jsx';

export default function Integrations() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get('/integrations/woocommerce/status');
      setStatus(data);
    } catch (e) {
      setError(apiError(e));
    } finally {
      setLoading(false);
    }
  }

  async function syncNow() {
    setSyncing(true);
    setError('');
    setResult('');
    try {
      const { data } = await api.post('/integrations/woocommerce/sync');
      setResult(data.message);
      await load();
    } catch (e) {
      setError(apiError(e));
    } finally {
      setSyncing(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) return <Loader label="Checking connection…" />;

  return (
    <div className="space-y-3 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold">Integrations</h1>
        <p className="text-xs text-gray-500">Connect your WooCommerce store to sync customers and orders.</p>
      </div>
      {error && <ErrorAlert message={error} onRetry={load} />}
      {result && (
        <div className="rounded-md bg-green-50 border border-green-200 p-3 text-xs text-green-700">
          {result}
        </div>
      )}
      {!status ? (
        <Card>
          <EmptyState title="Status unavailable" />
        </Card>
      ) : (
        <Card>
          <div className="space-y-2 text-xs">
            <p>
              Mode:{' '}
              {status.mode === 'live' ? (
                <StatusBadge value="completed" />
              ) : (
                <StatusBadge value="pending" />
              )}{' '}
              <span className="font-medium">{status.mode === 'live' ? 'Live store' : 'Demo mode'}</span>
            </p>
            <p className="text-gray-600">
              {status.configured
                ? 'Store credentials are configured on the backend.'
                : 'No store connected — set WC_STORE_URL / keys in the backend .env.'}
            </p>
            {status.store_url && <p className="text-gray-600">Store: {status.store_url}</p>}
            {status.key_hint && <p className="text-gray-600">Key: {status.key_hint} (secret never exposed)</p>}
            <p className="text-gray-600">
              Last sync: {status.last_sync_at ? new Date(status.last_sync_at).toLocaleString() : 'Never'}
            </p>
            <p className="text-gray-600">
              Synced: {status.customers_synced} customers · {status.orders_synced} orders
            </p>
            {status.message && <p className="text-gray-500">{status.message}</p>}
            <div className="pt-2">
              <button className={btnPrimary} onClick={syncNow} disabled={syncing}>
                {syncing ? 'Syncing…' : status.configured ? 'Sync now (live)' : 'Load demo data'}
              </button>
            </div>
            <p className="text-[11px] text-gray-400">
              {status.configured
                ? 'Pulls customers + orders from your store via the WooCommerce REST API. Existing records are updated by WooCommerce ID — no duplicates.'
                : 'Syncing now loads realistic sample data labelled “demo”. To go live, add WC_STORE_URL, WC_CONSUMER_KEY and WC_CONSUMER_SECRET to woocommerce_crm_backend/.env and restart the API.'}
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
