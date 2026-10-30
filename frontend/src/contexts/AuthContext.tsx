import React, { createContext, useContext, useState, useEffect } from "react";
import { User } from "../types";
import { api } from "../services/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  loginWithGoogle: (payload: { id_token?: string; code?: string; redirect_uri?: string }) => Promise<void>;
  register: (email: string, pass: string, name: string, confirmPass?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updateProfile: (payload: { full_name?: string; avatar_url?: string }) => Promise<User>;
  uploadAvatar: (file: File) => Promise<User>;
  deleteAvatar: () => Promise<User>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("lifebook_token"));
  const [loading, setLoading] = useState(true);

  const isAuthenticated = Boolean(user && token);

  useEffect(() => {
    async function initAuth() {
      const storedToken = localStorage.getItem("lifebook_token");
      if (storedToken) {
        try {
          const me = await api.getMe();
          setUser(me);
          setToken(storedToken);
          setLoading(false);
          return;
        } catch {
          // Token expired or invalid: clear session
          localStorage.removeItem("lifebook_token");
          localStorage.removeItem("lifebook_user");
          setUser(null);
          setToken(null);
        }
      } else {
        setUser(null);
        setToken(null);
      }
      setLoading(false);
    }

    initAuth();
  }, []);

  const login = async (email: string, pass: string) => {
    const res = await api.login(email, pass);
    setUser(res.user);
    setToken(res.access_token);
  };

  const loginWithGoogle = async (payload: { id_token?: string; code?: string; redirect_uri?: string }) => {
    const res = await api.loginWithGoogle(payload);
    setUser(res.user);
    setToken(res.access_token);
  };

  const register = async (email: string, pass: string, name: string, confirmPass?: string) => {
    const res = await api.register(email, pass, name, confirmPass);
    setUser(res.user);
    setToken(res.access_token);
  };

  const logout = async () => {
    await api.logout();
    setUser(null);
    setToken(null);
  };

  const refreshUser = async () => {
    try {
      const me = await api.getMe();
      setUser(me);
    } catch {
      // If refresh fails due to invalid session, logout
      await logout();
    }
  };

  const updateProfile = async (payload: { full_name?: string; avatar_url?: string }) => {
    const updated = await api.updateProfile(payload);
    setUser(updated);
    return updated;
  };

  const uploadAvatar = async (file: File) => {
    const updated = await api.uploadAvatar(file);
    setUser(updated);
    return updated;
  };

  const deleteAvatar = async () => {
    const updated = await api.deleteAvatar();
    setUser(updated);
    return updated;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated,
        loading,
        login,
        loginWithGoogle,
        register,
        logout,
        refreshUser,
        updateProfile,
        uploadAvatar,
        deleteAvatar
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};
