/**
 * Axios instance with full auth interceptors.
 * - Attaches Authorization: Bearer {access_token} on every request
 * - On 401: attempts silent token refresh via POST /api/auth/refresh
 * - On refresh success: retries the original request
 * - On refresh failure: clears auth state and redirects to /admin/login
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "../store/authStore";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// ─── Request interceptor ─────────────────────────────────────────────────────
// Attach Bearer token from authStore to every outgoing request.
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const { accessToken } = useAuthStore.getState();
    if (accessToken) {
      config.headers.set("Authorization", `Bearer ${accessToken}`);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Token refresh queue ─────────────────────────────────────────────────────
// Prevents multiple concurrent refresh calls when several requests 401 at once.
let isRefreshing = false;
let pendingQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function drainQueue(token: string | null, err: unknown = null) {
  pendingQueue.forEach(({ resolve, reject }) => {
    if (token) resolve(token);
    else reject(err);
  });
  pendingQueue = [];
}

// ─── Response interceptor ────────────────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Only intercept 401s; skip the refresh endpoint itself to avoid loops.
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      originalRequest.url !== "/api/auth/refresh"
    ) {
      const { refreshToken, setAccessToken, clearAuth } = useAuthStore.getState();

      if (!refreshToken) {
        clearAuth();
        window.location.href = "/admin/login";
        return Promise.reject(new Error("Session expired. Please log in again."));
      }

      if (isRefreshing) {
        // Queue this request until the refresh resolves.
        return new Promise((resolve, reject) => {
          pendingQueue.push({
            resolve: (newToken: string) => {
              originalRequest.headers.set("Authorization", `Bearer ${newToken}`);
              resolve(api(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post(`${BASE_URL}/api/auth/refresh`, {
          refresh: refreshToken,
        });
        const newAccessToken: string = data.access;
        setAccessToken(newAccessToken);
        drainQueue(newAccessToken);
        originalRequest.headers.set("Authorization", `Bearer ${newAccessToken}`);
        return api(originalRequest);
      } catch (refreshError) {
        drainQueue(null, refreshError);
        clearAuth();
        window.location.href = "/admin/login";
        return Promise.reject(new Error("Session expired. Please log in again."));
      } finally {
        isRefreshing = false;
      }
    }

    // Normalize error message for all other errors.
    const message =
      (error.response?.data as Record<string, string>)?.message ||
      (error.response?.data as Record<string, string>)?.error ||
      (error.response?.data as Record<string, string>)?.detail ||
      error.message ||
      "An unexpected error occurred";
    return Promise.reject(new Error(message));
  }
);

export default api;
