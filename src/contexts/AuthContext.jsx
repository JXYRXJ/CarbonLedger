import { createContext, useContext, useEffect, useMemo, useState, useCallback } from "react";
import { authApi } from "@/services/authApi.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const raw = localStorage.getItem("cl_user");
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(false);

  const persist = (token, refreshToken, userData) => {
    if (token) localStorage.setItem("cl_token", token);
    if (refreshToken) localStorage.setItem("cl_refresh", refreshToken);
    if (userData) localStorage.setItem("cl_user", JSON.stringify(userData));
    setUser(userData ?? null);
  };

  const login = useCallback(async (creds) => {
    setLoading(true);
    try {
      const data = await authApi.login(creds);
      persist(data.access_token, data.refresh_token, data.user);
      return data.user;
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (payload) => {
    setLoading(true);
    try {
      const data = await authApi.register(payload);
      persist(data.access_token, data.refresh_token, data.user);
      return data.user;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      const refreshToken = localStorage.getItem("cl_refresh");
      await authApi.logout({ refresh_token: refreshToken });
    } catch { /* ignore */ }
    localStorage.removeItem("cl_token");
    localStorage.removeItem("cl_refresh");
    localStorage.removeItem("cl_user");
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, isAuthenticated: !!user, login, register, logout, setUser }),
    [user, loading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
