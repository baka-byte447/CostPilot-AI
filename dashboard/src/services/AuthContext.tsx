import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import api, { authLogin, authRegister } from "./api";

interface User {
  user_id: number;
  email: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

const STORAGE_KEY_TOKEN = "costpilot_token";
const STORAGE_KEY_USER = "costpilot_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // ── Restore session from localStorage on mount ──
  useEffect(() => {
    const savedToken = localStorage.getItem(STORAGE_KEY_TOKEN);
    const savedUser = localStorage.getItem(STORAGE_KEY_USER);
    if (savedToken && savedUser) {
      try {
        const parsed = JSON.parse(savedUser) as User;
        setToken(savedToken);
        setUser(parsed);
      } catch {
        localStorage.removeItem(STORAGE_KEY_TOKEN);
        localStorage.removeItem(STORAGE_KEY_USER);
      }
    }
    setLoading(false);
  }, []);

  // ── Keep axios headers in sync with token/user ──
  useEffect(() => {
    if (token && user) {
      api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      api.defaults.headers.common["X-User-Id"] = String(user.user_id);
    } else {
      delete api.defaults.headers.common["Authorization"];
      delete api.defaults.headers.common["X-User-Id"];
    }
  }, [token, user]);

  const persistSession = useCallback((t: string, u: User) => {
    localStorage.setItem(STORAGE_KEY_TOKEN, t);
    localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(u));
    setToken(t);
    setUser(u);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await authLogin(email, password);
    const { access_token, user_id, email: returnedEmail } = res.data;
    persistSession(access_token, { user_id, email: returnedEmail });
  }, [persistSession]);

  const register = useCallback(async (email: string, password: string) => {
    const res = await authRegister(email, password);
    const { access_token, user_id, email: returnedEmail } = res.data;
    persistSession(access_token, { user_id, email: returnedEmail });
  }, [persistSession]);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY_TOKEN);
    localStorage.removeItem(STORAGE_KEY_USER);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
