import { useState } from 'react';
import api, { apiError } from '../lib/api.js';
import { Modal, btnPrimary, btnGhost, inputCls } from './ui.jsx';

/** Create follow-up modal (used on Follow-ups page + customer profile). */
export function FollowUpModal({ open, onClose, customers, presetCustomerId, onCreated }) {
  const [form, setForm] = useState({
    customer_id: presetCustomerId || '',
    title: '',
    due_date: '',
    notes: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload = {
        customer_id: Number(presetCustomerId || form.customer_id),
        title: form.title,
        due_date: new Date(form.due_date).toISOString(),
        notes: form.notes || null,
      };
      const { data } = await api.post('/followups', payload);
      onCreated?.(data);
      setForm({ customer_id: presetCustomerId || '', title: '', due_date: '', notes: '' });
      onClose();
    } catch (e) {
      setError(apiError(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open={open} title="Create follow-up" onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        {error && <p className="text-sm text-red-600">{error}</p>}
        {!presetCustomerId && (
          <select
            className={inputCls}
            value={form.customer_id}
            onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
            required
          >
            <option value="">Select customer…</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.first_name} {c.last_name} — {c.email}
              </option>
            ))}
          </select>
        )}
        <input
          className={inputCls}
          placeholder="Title (e.g. Call about order #5003)"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          required
        />
        <input
          type="datetime-local"
          className={inputCls}
          value={form.due_date}
          onChange={(e) => setForm({ ...form, due_date: e.target.value })}
          required
        />
        <textarea
          className={inputCls}
          placeholder="Notes (optional)"
          rows={3}
          value={form.notes}
          onChange={(e) => setForm({ ...form, notes: e.target.value })}
        />
        <div className="flex justify-end gap-2">
          <button type="button" className={btnGhost} onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className={btnPrimary} disabled={saving}>
            {saving ? 'Saving…' : 'Create'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

/** Add / edit customer modal (POST /customers, PUT /customers/{id}). */
export function CustomerModal({ open, onClose, initial, onSaved }) {
  const isEdit = !!initial?.id;
  const [form, setForm] = useState({
    email: initial?.email || '',
    first_name: initial?.first_name || '',
    last_name: initial?.last_name || '',
    phone: initial?.phone || '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      let data;
      if (isEdit) {
        ({ data } = await api.put(`/customers/${initial.id}`, form));
      } else {
        ({ data } = await api.post('/customers', form));
      }
      onSaved?.(data);
      onClose();
    } catch (e) {
      setError(apiError(e));
    } finally {
      setSaving(false);
    }
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <Modal open={open} title={isEdit ? 'Edit customer' : 'Add customer'} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        {error && <p className="text-sm text-red-600">{error}</p>}
        <input className={inputCls} type="email" placeholder="Email" value={form.email} onChange={set('email')} required />
        <div className="grid grid-cols-2 gap-2">
          <input className={inputCls} placeholder="First name" value={form.first_name} onChange={set('first_name')} />
          <input className={inputCls} placeholder="Last name" value={form.last_name} onChange={set('last_name')} />
        </div>
        <input className={inputCls} placeholder="Phone (optional)" value={form.phone} onChange={set('phone')} />
        <div className="flex justify-end gap-2">
          <button type="button" className={btnGhost} onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className={btnPrimary} disabled={saving}>
            {saving ? 'Saving…' : isEdit ? 'Save changes' : 'Add customer'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

/** Log an interaction (call / email / meeting / note). Manual record only — no auto-sending. */
export function InteractionForm({ customerId, onAdded }) {
  const [form, setForm] = useState({ interaction_type: 'call', description: '', outcome: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [ok, setOk] = useState('');

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError('');
    setOk('');
    try {
      const { data } = await api.post('/interactions', {
        customer_id: customerId,
        interaction_type: form.interaction_type,
        description: form.description,
        outcome: form.outcome || null,
      });
      setOk('Interaction recorded.');
      setForm({ interaction_type: 'call', description: '', outcome: '' });
      onAdded?.(data);
    } catch (e) {
      setError(apiError(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-2">
      <h3 className="font-semibold text-xs">Log interaction</h3>
      {error && <p className="text-xs text-red-600">{error}</p>}
      {ok && <p className="text-xs text-green-600">{ok}</p>}
      <div className="grid grid-cols-2 gap-2">
        <select
          className={inputCls}
          value={form.interaction_type}
          onChange={(e) => setForm({ ...form, interaction_type: e.target.value })}
        >
          <option value="call">Call</option>
          <option value="email">Email</option>
          <option value="meeting">Meeting</option>
          <option value="note">Note</option>
        </select>
        <input
          className={inputCls}
          placeholder="Outcome (optional)"
          value={form.outcome}
          onChange={(e) => setForm({ ...form, outcome: e.target.value })}
        />
      </div>
      <textarea
        className={inputCls}
        placeholder="What happened? (e.g. Called — customer asked for invoice copy, sent manually)"
        rows={3}
        value={form.description}
        onChange={(e) => setForm({ ...form, description: e.target.value })}
        required
      />
      <button type="submit" className={btnPrimary} disabled={saving}>
        {saving ? 'Saving…' : 'Record interaction'}
      </button>
    </form>
  );
}

/** Add a manual admin note to a customer profile. */
export function NoteForm({ customerId, onAdded }) {
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const { data } = await api.post(`/customers/${customerId}/notes`, { note });
      setNote('');
      onAdded?.(data);
    } catch (e) {
      setError(apiError(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-2">
      <h3 className="font-semibold text-xs">Add note</h3>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <textarea
        className={inputCls}
        placeholder="Internal note (only visible in CRM)…"
        rows={4}
        value={note}
        onChange={(e) => setNote(e.target.value)}
        required
      />
      <button type="submit" className={btnPrimary} disabled={saving}>
        {saving ? 'Saving…' : 'Add note'}
      </button>
    </form>
  );
}
