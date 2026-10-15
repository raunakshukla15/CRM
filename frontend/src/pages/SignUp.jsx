import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiError } from '../lib/api.js';
import { useAuth } from '../lib/auth.jsx';
import { AuthFooter, AuthShell, btnPrimary, inputCls } from './AuthShell.jsx';

export default function SignUp() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm_password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    if (form.password !== form.confirm_password) {
      setError('Passwords do not match.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await register(form.full_name.trim(), form.email.trim(), form.password, form.confirm_password);
      navigate('/');
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell title="Create your account" subtitle="Start managing customers in minutes.">
      <form onSubmit={submit} className="space-y-3">
        {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-2">{error}</p>}
        <input className={inputCls} placeholder="Full name" value={form.full_name} onChange={set('full_name')} required autoComplete="name" />
        <input className={inputCls} type="email" placeholder="Email address" value={form.email} onChange={set('email')} required autoComplete="email" />
        <input className={inputCls} type="password" placeholder="Password (min 8 chars, letter + number)" value={form.password} onChange={set('password')} required autoComplete="new-password" />
        <input className={inputCls} type="password" placeholder="Confirm password" value={form.confirm_password} onChange={set('confirm_password')} required autoComplete="new-password" />
        <button type="submit" className={`${btnPrimary} w-full`} disabled={busy}>
          {busy ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <AuthFooter to="/signin" text="Already have an account?" label="Sign in" />
    </AuthShell>
  );
}
