import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api, { apiError } from '../lib/api.js';
import { AuthShell, btnPrimary, inputCls } from './AuthShell.jsx';

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get('token') || '';
  const [form, setForm] = useState({ new_password: '', confirm_password: '' });
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (form.new_password !== form.confirm_password) {
      setError('Passwords do not match.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await api.post('/auth/reset-password', { token, ...form });
      setDone(true);
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell title="Choose a new password" subtitle="Your reset link is valid for 1 hour.">
      {!token ? (
        <p className="text-sm text-red-600">Missing reset token. Use the link from your email.</p>
      ) : done ? (
        <p className="text-sm text-green-700 bg-green-50 border border-green-200 rounded-md p-3">
          Password updated. <Link to="/signin" className="underline font-medium">Sign in</Link> with your new password.
        </p>
      ) : (
        <form onSubmit={submit} className="space-y-3">
          {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-2">{error}</p>}
          <input className={inputCls} type="password" placeholder="New password (min 8 chars, letter + number)" value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} required autoComplete="new-password" />
          <input className={inputCls} type="password" placeholder="Confirm new password" value={form.confirm_password} onChange={(e) => setForm({ ...form, confirm_password: e.target.value })} required autoComplete="new-password" />
          <button type="submit" className={`${btnPrimary} w-full`} disabled={busy}>
            {busy ? 'Updating…' : 'Update password'}
          </button>
        </form>
      )}
    </AuthShell>
  );
}
