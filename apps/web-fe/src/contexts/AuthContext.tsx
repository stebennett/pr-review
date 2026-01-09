import {
  createContext,
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, clearAuthToken, hasAuthToken } from "../services/api";
import type { User, LoginResponse } from "../types";

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: () => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    if (!hasAuthToken()) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const response = await api.get<User>("/api/auth/me");
      setUser(response);
    } catch {
      // Token is invalid or expired
      clearAuthToken();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = useCallback(async () => {
    const response = await api.get<LoginResponse>("/api/auth/login");
    window.location.href = response.url;
  }, []);

  const logout = useCallback(() => {
    clearAuthToken();
    setUser(null);
    window.location.href = "/login";
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
