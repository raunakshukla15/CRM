export function Loader({ label = 'Loading…' }) {
  return <div className="py-10 text-center text-gray-500 animate-pulse text-sm">{label}</div>;
}

export function ErrorAlert({ message, onRetry }) {
  if (!message) return null;
  return (
    <div className="mb-4 rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700 flex items-center justify-between gap-2">
      <span>{message}</span>
      {onRetry && (
        <button onClick={onRetry} className="underline font-medium shrink-0">
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, hint, icon }) {
  return (
    <div className="py-8 text-center">
      {icon && <div className="text-3xl text-gray-300 mb-1">{icon}</div>}
      <p className="text-gray-700 font-medium text-sm">{title}</p>
      {hint && <p className="text-gray-400 text-xs mt-1">{hint}</p>}
    </div>
  );
}

const ICON_BG = {
  blue: 'bg-blue-100 text-blue-600',
  purple: 'bg-purple-100 text-purple-600',
  green: 'bg-green-100 text-green-600',
  orange: 'bg-orange-100 text-orange-600',
  yellow: 'bg-yellow-100 text-yellow-600',
  red: 'bg-red-100 text-red-500',
};

export function StatCard({ label, value, sub, icon, color = 'blue' }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex items-center gap-3">
      {icon && (
        <span className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${ICON_BG[color]}`}>
          {icon}
        </span>
      )}
      <div>
        <p className="text-[11px] uppercase tracking-wide text-gray-400">{label}</p>
        <p className="text-xl font-bold">{value}</p>
        {sub && <p className="text-[11px] text-gray-400">{sub}</p>}
      </div>
    </div>
  );
}

export function Card({ title, action, children, className = '' }) {
  return (
    <section className={`bg-white rounded-xl shadow-sm border border-gray-100 p-4 ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-semibold text-sm">{title}</h2>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

const badgeColors = {
  completed: 'bg-green-100 text-green-700',
  paid: 'bg-green-100 text-green-700',
  fulfilled: 'bg-green-100 text-green-700',
  pending: 'bg-yellow-100 text-yellow-700',
  'on-hold': 'bg-yellow-100 text-yellow-700',
  processing: 'bg-blue-100 text-blue-700',
  partial: 'bg-blue-100 text-blue-700',
  unfulfilled: 'bg-gray-100 text-gray-600',
  cancelled: 'bg-gray-100 text-gray-500',
  failed: 'bg-red-100 text-red-600',
  refunded: 'bg-purple-100 text-purple-700',
  VIP: 'bg-yellow-100 text-yellow-700',
  Active: 'bg-green-100 text-green-700',
  Lead: 'bg-gray-100 text-gray-600',
  Churned: 'bg-red-100 text-red-600',
  overdue: 'bg-red-100 text-red-600',
};

export function StatusBadge({ value }) {
  const cls = badgeColors[value] || 'bg-gray-100 text-gray-600';
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-medium ${cls}`}>
      {value}
    </span>
  );
}

export function Avatar({ first, last, size = 'w-12 h-12 text-base' }) {
  const init = `${(first || ' ')[0] || ''}${(last || ' ')[0] || ''}`.toUpperCase() || '?';
  return (
    <span
      className={`${size} rounded-full bg-indigo-100 text-indigo-500 flex items-center justify-center font-semibold shrink-0`}
    >
      {init}
    </span>
  );
}

export function Modal({ open, title, onClose, children }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-lg w-full max-w-md p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 px-2">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export const inputCls =
  'w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white';
export const btnPrimary =
  'bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 whitespace-nowrap';
export const btnGhost =
  'border border-gray-200 px-4 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50';
export const linkAction = 'text-indigo-600 hover:underline text-xs font-medium whitespace-nowrap';
