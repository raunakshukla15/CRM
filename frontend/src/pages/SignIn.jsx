import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiError } from '../lib/api.js';
import { useAuth } from '../lib/auth.jsx';
import { AuthFooter, AuthShell, btnPrimary, inputCls } from './AuthShell.jsx';

export default function SignIn() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await login(email.trim(), password);
      navigate('/');
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell title="Welcome back" subtitle="Sign in to your KilloKart account.">
      <form onSubmit={submit} className="space-y-3">
        {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-2">{error}</p>}
        <input className={inputCls} type="email" placeholder="Email address" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        <input className={inputCls} type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
        <button type="submit" className={`${btnPrimary} w-full`} disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
      <div className="flex justify-between mt-3 text-sm">
        <a href="/forgot-password" className="text-indigo-600 hover:underline">Forgot password?</a>
        <span />
      </div>
      <AuthFooter to="/signup" text="New to KilloKart?" label="Create an account" />
    </AuthShell>
  );
}
