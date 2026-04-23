import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import axios from "axios";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface User {
  id: number;
  name: string;
  email: string;
  company?: string;
  plan?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
}

interface RegisterData {
  name: string;
  email: string;
  company: string;
  provider: string;
  password: string;
  confirmPassword: string;
}

const AuthContext = createContext<AuthContextType | null>(null);

const TOKEN_KEY = "costpilot_token";
const USER_KEY = "costpilot_user";

function loadStored<T>(key: string): T | null {
  try {
    const v = localStorage.getItem(key);
    return v ? JSON.parse(v) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(() => loadStored<User>(USER_KEY));

  useEffect(() => {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    } else {
      localStorage.removeItem(TOKEN_KEY);
      delete axios.defaults.headers.common["Authorization"];
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(USER_KEY);
    }
  }, [user]);

  useEffect(() => {
    if (!token) return;
    axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    axios
      .get(`${API}/auth/me`)
      .then(r => setUser(r.data))
      .catch(() => {
        setToken(null);
        setUser(null);
      });
  }, []);

  async function login(email: string, password: string) {
    if (!email || !password) throw new Error("Email and password are required.");
    try {
      const { data } = await axios.post(`${API}/auth/login`, { email, password });
      setToken(data.access_token);
      setUser(data.user);
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response) {
        throw new Error(err.response.data?.detail ?? "Login failed.");
      }
      throw new Error("Cannot reach the server. Is the backend running?");
    }
  }

  async function register(data: RegisterData) {
    if (!data.name || !data.email || !data.password)
      throw new Error("Name, email, and password are required.");
    if (data.password !== data.confirmPassword)
      throw new Error("Passwords do not match.");
    if (data.password.length < 6)
      throw new Error("Password must be at least 6 characters.");
    try {
      const { data: resp } = await axios.post(`${API}/auth/register`, {
        email: data.email,
        password: data.password,
        name: data.name,
        company: data.company,
      });
      setToken(resp.access_token);
      setUser(resp.user);
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response) {
        throw new Error(err.response.data?.detail ?? "Registration failed.");
      }
      throw new Error("Cannot reach the server. Is the backend running?");
    }
  }

  function logout() {
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
