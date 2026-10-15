import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import api from './api.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get('/auth/me');
      setUser(data);
      return data;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  async function login(email, password) {
    const { data } = await api.post('/auth/login', { email, password });
    setUser(data);
    return data;
  }

  async function register(full_name, email, password, confirm_password) {
    const { data } = await api.post('/auth/register', {
      full_name,
      email,
      password,
      confirm_password,
    });
    setUser(data);
    return data;
  }

  async function logout() {
    try {
      await api.post('/auth/logout');
    } finally {
      setUser(null);
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
