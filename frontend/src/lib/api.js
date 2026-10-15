import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1',
  timeout: 20000,
  // Session cookie (HTTP-only) must travel with every request, including
  // cross-origin (Netlify → Render). No tokens in localStorage, ever.
  withCredentials: true,
});

export function apiError(e) {
  if (e?.response?.data?.detail) {
    const d = e.response.data.detail;
    return typeof d === 'string' ? d : JSON.stringify(d);
  }
  if (e?.code === 'ERR_NETWORK') return 'Cannot reach the backend. Is FastAPI running on :8000?';
  return e?.message || 'Something went wrong';
}

export default api;
