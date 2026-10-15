import { useState } from 'react';
import api, { apiError } from '../lib/api.js';
import { AuthFooter, AuthShell, btnPrimary, inputCls } from './AuthShell.jsx';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await api.post('/auth/forgot-password', { email: email.trim() });
      setDone(true);
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell title="Reset password" subtitle="We'll email you a reset link if the address is registered.">
      {done ? (
        <p className="text-sm text-green-700 bg-green-50 border border-green-200 rounded-md p-3">
          If an account exists for this email, a reset link has been sent. Check your inbox
          (and spam folder). The link expires in 1 hour.
        </p>
      ) : (
        <form onSubmit={submit} className="space-y-3">
          {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-2">{error}</p>}
          <input className={inputCls} type="email" placeholder="Email address" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
          <button type="submit" className={`${btnPrimary} w-full`} disabled={busy}>
            {busy ? 'Sending…' : 'Send reset link'}
          </button>
        </form>
      )}
      <AuthFooter to="/signin" text="Remembered it?" label="Back to sign in" />
    </AuthShell>
  );
}
