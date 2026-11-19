import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { api, clearTokens, saveTokens } from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionStorage.getItem('cc_access')) {
      setLoading(false);
      return;
    }
    api('/me/').then(setUser).catch(() => {
      clearTokens();
      setUser(null);
    }).finally(() => setLoading(false));
  }, []);

  async function login(username, password) {
    const tokens = await api('/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }, false);
    saveTokens(tokens);
    const profile = await api('/me/');
    setUser(profile);
    return profile;
  }

  function logout() {
    clearTokens();
    setUser(null);
  }

  const value = useMemo(() => ({ user, loading, login, logout, setUser }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider');
  return context;
}
