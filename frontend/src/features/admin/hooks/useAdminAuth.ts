import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

interface LoginPayload {
  email: string;
  password: string;
}

interface LoginResponseData {
  access: string;
  refresh: string;
  role: "SYS_ADMIN" | "TAX_ADMIN";
  admin_id: string;
  email: string;
  name: string;
}

// Backend wraps all responses: { success, message, data: { ... } }
interface LoginResponse {
  success: boolean;
  message: string;
  data: LoginResponseData;
}

interface UseAdminAuthReturn {
  login: (payload: LoginPayload) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export function useAdminAuth(): UseAdminAuthReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const login = async (payload: LoginPayload) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.post<LoginResponse>("/api/auth/login", payload);
      const { access, refresh, role, admin_id, email } = response.data.data;
      setAuth({ accessToken: access, refreshToken: refresh, role, adminId: admin_id, email });
      navigate("/admin/dashboard", { replace: true });
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number } };
      if (axiosErr?.response?.status === 401) {
        setError("Invalid email or password. Please try again.");
      } else if (axiosErr?.response?.status === 429) {
        setError("Too many login attempts. Please wait a moment.");
      } else {
        setError(err instanceof Error ? err.message : "Login failed. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return { login, isLoading, error };
}
