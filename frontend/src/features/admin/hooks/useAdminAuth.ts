import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

const PENDING_OTP_KEY = "ghana-tax-pending-otp";

interface LoginPayload {
  email: string;
  password: string;
}

interface PendingOtpSession {
  pendingToken: string;
  email: string;
  expiresAt: number;
  otpExpiresAt: number;
}

interface LoginResponseData {
  pending_token: string;
  scope: "otp_pending";
  expires_in: number;
  otp_expires_in: number;
  email: string;
}

interface AuthTokensResponseData {
  access: string;
  refresh: string;
  role: "SYS_ADMIN" | "TAX_ADMIN";
  admin_id: string;
  email: string;
  name: string;
}

interface ResendOtpResponseData extends LoginResponseData {
  resend_count: number;
}

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

interface UseAdminAuthReturn {
  login: (payload: LoginPayload) => Promise<void>;
  verifyOtp: (code: string) => Promise<void>;
  resendOtp: () => Promise<PendingOtpSession>;
  getPendingOtpSession: () => PendingOtpSession | null;
  clearPendingOtpSession: () => void;
  isLoading: boolean;
  error: string | null;
  remainingAttempts: number | null;
}

function savePendingOtpSession(data: LoginResponseData | ResendOtpResponseData): PendingOtpSession {
  const now = Date.now();
  const session = {
    pendingToken: data.pending_token,
    email: data.email || getPendingOtpSession()?.email || "",
    expiresAt: now + data.expires_in * 1000,
    otpExpiresAt: now + data.otp_expires_in * 1000,
  };
  sessionStorage.setItem(PENDING_OTP_KEY, JSON.stringify(session));
  return session;
}

function getPendingOtpSession(): PendingOtpSession | null {
  const raw = sessionStorage.getItem(PENDING_OTP_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as PendingOtpSession;
    if (!parsed.pendingToken || parsed.expiresAt <= Date.now()) {
      sessionStorage.removeItem(PENDING_OTP_KEY);
      return null;
    }
    return parsed;
  } catch {
    sessionStorage.removeItem(PENDING_OTP_KEY);
    return null;
  }
}

function clearPendingOtpSession() {
  sessionStorage.removeItem(PENDING_OTP_KEY);
}

export function useAdminAuth(): UseAdminAuthReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [remainingAttempts, setRemainingAttempts] = useState<number | null>(null);
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const login = async (payload: LoginPayload) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.post<ApiResponse<LoginResponseData>>("/api/auth/login/", payload);
      savePendingOtpSession(response.data.data);
      navigate("/admin/verify-otp", { replace: true });
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

  const verifyOtp = async (code: string) => {
    const pending = getPendingOtpSession();
    if (!pending) {
      clearPendingOtpSession();
      navigate("/admin/login", { replace: true, state: { message: "Verification expired. Please sign in again." } });
      return;
    }

    setIsLoading(true);
    setError(null);
    setRemainingAttempts(null);
    try {
      const response = await api.post<ApiResponse<AuthTokensResponseData>>(
        "/api/auth/verify-otp/",
        { code },
        { headers: { Authorization: `Bearer ${pending.pendingToken}` } }
      );
      const { access, refresh, role, admin_id, email } = response.data.data;
      clearPendingOtpSession();
      setAuth({ accessToken: access, refreshToken: refresh, role, adminId: admin_id, email });
      navigate("/admin/dashboard", { replace: true });
    } catch (err: unknown) {
      const response = (err as { response?: { status?: number; data?: { errors?: { remaining_attempts?: number } } } }).response;
      if (typeof response?.data?.errors?.remaining_attempts === "number") {
        setRemainingAttempts(response.data.errors.remaining_attempts);
        setError("Invalid verification code.");
      } else if (response?.status === 401) {
        clearPendingOtpSession();
        navigate("/admin/login", { replace: true, state: { message: "Verification expired. Please sign in again." } });
      } else {
        setError(err instanceof Error ? err.message : "Verification failed. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const resendOtp = async () => {
    const pending = getPendingOtpSession();
    if (!pending) {
      clearPendingOtpSession();
      navigate("/admin/login", { replace: true, state: { message: "Verification expired. Please sign in again." } });
      throw new Error("Verification expired.");
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await api.post<ApiResponse<ResendOtpResponseData>>(
        "/api/auth/resend-otp/",
        {},
        { headers: { Authorization: `Bearer ${pending.pendingToken}` } }
      );
      return savePendingOtpSession({ ...response.data.data, email: pending.email });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not resend code. Please try again.");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    login,
    verifyOtp,
    resendOtp,
    getPendingOtpSession,
    clearPendingOtpSession,
    isLoading,
    error,
    remainingAttempts,
  };
}
