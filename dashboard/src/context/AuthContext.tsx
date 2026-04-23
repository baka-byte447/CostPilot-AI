import { createContext, useContext, useState, useEffect } from "react";

interface User {
  name: string;
  email: string;
  company?: string;
  provider?: string;
}

interface AuthContextType {
  user: User | null;
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

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const stored = localStorage.getItem("costpilot_user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem("costpilot_user", JSON.stringify(user));
    } else {
      localStorage.removeItem("costpilot_user");
    }
  }, [user]);

  async function login(email: string, password: string) {
    if (!email || !password) throw new Error("Email and password are required.");
    const stored = localStorage.getItem(`costpilot_account_${email}`);
    if (!stored) throw new Error("No account found with this email.");
    const account = JSON.parse(stored);
    if (account.password !== password) throw new Error("Incorrect password.");
    setUser({ name: account.name, email: account.email, company: account.company });
  }

  async function register(data: RegisterData) {
    if (!data.name || !data.email || !data.password)
      throw new Error("Name, email, and password are required.");
    if (data.password !== data.confirmPassword)
      throw new Error("Passwords do not match.");
    if (data.password.length < 6)
      throw new Error("Password must be at least 6 characters.");
    const key = `costpilot_account_${data.email}`;
    if (localStorage.getItem(key))
      throw new Error("An account with this email already exists.");
    localStorage.setItem(key, JSON.stringify(data));
    setUser({ name: data.name, email: data.email, company: data.company, provider: data.provider });
  }

  function logout() {
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
