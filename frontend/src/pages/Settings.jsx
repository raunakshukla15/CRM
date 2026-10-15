import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { apiError } from '../lib/api.js';
import { useAuth } from '../lib/auth.jsx';
import { Card, ErrorAlert, Modal, btnPrimary, btnGhost, inputCls } from '../components/ui.jsx';

export default function Settings() {
  const { user, refresh, logout } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState(user?.full_name || '');
  const [ok, setOk] = useState('');
  const [error, setError] = useState('');
  const [pw, setPw] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [delPw, setDelPw] = useState('');
  const [delOpen, setDelOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  async function saveProfile(e) {
    e.preventDefault();
    setError('');
    setOk('');
    try {
      await api.put('/auth/me', { full_name: name.trim() });
      await refresh();
      setOk('Profile updated.');
    } catch (err) {
      setError(apiError(err));
    }
  }

  async function changePassword(e) {
    e.preventDefault();
    if (pw.new_password !== pw.confirm_password) {
      setError('New passwords do not match.');
      return;
    }
    setError('');
    setOk('');
    setBusy(true);
    try {
      const { data } = await api.post('/auth/change-password', pw);
      setPw({ current_password: '', new_password: '', confirm_password: '' });
      setOk(`Password changed. ${data.sessions_revoked || 0} other session(s) signed out.`);
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function deleteAccount() {
    setError('');
    setBusy(true);
    try {
      await api.delete('/auth/account', { data: { password: delPw } });
      await logout();
      navigate('/signin');
    } catch (err) {
      setError(apiError(err));
      setBusy(false);
      setDelOpen(false);
    }
  }

  return (
    <div className="space-y-3 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold">Account settings</h1>
        <p className="text-xs text-gray-500">Signed in as {user?.email}</p>
      </div>
      {error && <ErrorAlert message={error} />}
      {ok && <div className="rounded-md bg-green-50 border border-green-200 p-3 text-xs text-green-700">{ok}</div>}

      <Card title="Profile">
        <form onSubmit={saveProfile} className="flex flex-col sm:flex-row gap-2">
          <input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} required maxLength={255} />
          <button type="submit" className={btnPrimary}>Save</button>
        </form>
      </Card>

      <Card title="Change password">
        <form onSubmit={changePassword} className="space-y-2">
          <input className={inputCls} type="password" placeholder="Current password" value={pw.current_password} onChange={(e) => setPw({ ...pw, current_password: e.target.value })} required autoComplete="current-password" />
          <input className={inputCls} type="password" placeholder="New password (min 8 chars, letter + number)" value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} required autoComplete="new-password" />
          <input className={inputCls} type="password" placeholder="Confirm new password" value={pw.confirm_password} onChange={(e) => setPw({ ...pw, confirm_password: e.target.value })} required autoComplete="new-password" />
          <button type="submit" className={btnPrimary} disabled={busy}>{busy ? 'Updating…' : 'Update password'}</button>
          <p className="text-[11px] text-gray-400">All other sessions are signed out when you change your password.</p>
        </form>
      </Card>

      <Card title="Delete account">
        <p className="text-xs text-gray-600 mb-2">
          Permanently deletes your account, all sessions, and <strong>all</strong> of your CRM
          records (customers, orders, communications, follow-ups, notes, activity history).
          This cannot be undone. Only a domain-only anonymized audit entry is kept.
        </p>
        <button onClick={() => { setDelPw(''); setDelOpen(true); }} className="px-4 py-2 rounded-md text-sm font-medium bg-red-600 text-white hover:bg-red-700">
          Delete my account…
        </button>
      </Card>

      <Modal open={delOpen} title="Delete account?" onClose={() => setDelOpen(false)}>
        <p className="text-sm text-gray-600 mb-3">
          Type your password to confirm permanent deletion of <strong>{user?.email}</strong> and
          every CRM record you own.
        </p>
        <input className={inputCls} type="password" placeholder="Confirm password" value={delPw} onChange={(e) => setDelPw(e.target.value)} autoComplete="current-password" />
        <div className="flex justify-end gap-2 mt-3">
          <button className={btnGhost} onClick={() => setDelOpen(false)}>Cancel</button>
          <button className="px-4 py-2 rounded-md text-sm font-medium bg-red-600 text-white hover:bg-red-700 disabled:opacity-50" disabled={!delPw || busy} onClick={deleteAccount}>
            {busy ? 'Deleting…' : 'Delete forever'}
          </button>
        </div>
      </Modal>
    </div>
  );
}
