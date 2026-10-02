import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { saasApi } from '../services/saasApi';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const clearSession = () => setUser(null);
  useEffect(() => {
    const unauthorized = () => clearSession();
    window.addEventListener('retainiq:unauthorized', unauthorized);
    saasApi('/api/auth/me').then(setUser).catch(clearSession).finally(() => setLoading(false));
    return () => window.removeEventListener('retainiq:unauthorized', unauthorized);
  }, []);
  const authenticate = async (mode, payload) => {
    const data = await saasApi(`/api/auth/${mode}`, { method: 'POST', body: JSON.stringify(payload) });
    setUser(data.user);
  };
  const logout = async () => {
    await saasApi('/api/auth/logout', { method: 'POST' }).catch(() => null);
    clearSession();
  };
  const value = useMemo(() => ({ user, loading, login: payload => authenticate('login', payload), logout }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);

