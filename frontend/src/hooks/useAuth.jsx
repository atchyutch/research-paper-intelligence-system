import { createContext, useContext, useState, useCallback } from 'react';
import { auth as authApi } from '../lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(authApi.isLoggedIn());

  const login = useCallback(async (email, password) => {
    await authApi.login(email, password);
    setIsAuthenticated(true);
  }, []);

  const register = useCallback(async (firstName, lastName, email, password) => {
    await authApi.register(firstName, lastName, email, password);
    // Auto-login after registration
    await authApi.login(email, password);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(() => {
    authApi.logout();
    setIsAuthenticated(false);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
