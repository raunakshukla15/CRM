import api from './api.js';

/** Relative time for activity feeds, e.g. "10 min ago". */
export function timeAgo(iso) {
  if (!iso) return '';
  const then = new Date(iso).getTime();
  const diff = Math.max(0, Date.now() - then);
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hr ago`;
  const days = Math.floor(hours / 24);
  return days === 1 ? 'yesterday' : `${days} days ago`;
}

export function initials(first = '', last = '') {
  return `${(first || ' ')[0] || ''}${(last || ' ')[0] || ''}`.toUpperCase() || '?';
}

export function money(v) {
  return `$${Number(v || 0).toFixed(2)}`;
}

export { api };
export { apiError } from './api.js';
