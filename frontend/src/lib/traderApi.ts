import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { useTraderAuthStore } from "../store/traderAuthStore";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const traderApi = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

traderApi.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const { accessToken } = useTraderAuthStore.getState();
    if (accessToken) {
      config.headers.set("Authorization", `Bearer ${accessToken}`);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

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

traderApi.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      originalRequest.url !== "/api/trader-auth/refresh/"
    ) {
      const { refreshToken, setAccessToken, clearAuth } = useTraderAuthStore.getState();

      if (!refreshToken) {
        clearAuth();
        window.location.href = "/trader/login";
        return Promise.reject(new Error("Session expired. Please log in again."));
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pendingQueue.push({
            resolve: (newToken: string) => {
              originalRequest.headers.set("Authorization", `Bearer ${newToken}`);
              resolve(traderApi(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post(`${BASE_URL}/api/trader-auth/refresh/`, {
          refresh: refreshToken,
        });
        const newAccessToken: string = data.data?.access ?? data.access;
        setAccessToken(newAccessToken);
        drainQueue(newAccessToken);
        originalRequest.headers.set("Authorization", `Bearer ${newAccessToken}`);
        return traderApi(originalRequest);
      } catch (refreshError) {
        drainQueue(null, refreshError);
        clearAuth();
        window.location.href = "/trader/login";
        return Promise.reject(new Error("Session expired. Please log in again."));
      } finally {
        isRefreshing = false;
      }
    }

    const message =
      (error.response?.data as Record<string, string>)?.message ||
      (error.response?.data as Record<string, string>)?.error ||
      (error.response?.data as Record<string, string>)?.detail ||
      error.message ||
      "An unexpected error occurred";
    return Promise.reject(Object.assign(new Error(message), { response: error.response }));
  }
);

export default traderApi;
