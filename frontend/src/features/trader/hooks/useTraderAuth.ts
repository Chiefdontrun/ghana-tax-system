import { useState } from "react";
import { useNavigate } from "react-router-dom";
import traderApi from "@/lib/traderApi";
import { useTraderAuthStore } from "@/store/traderAuthStore";

export function useTraderAuth() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const setAuth = useTraderAuthStore((state) => state.setAuth);
  const clearAuth = useTraderAuthStore((state) => state.clearAuth);

  const requestOtp = async (phoneNumber: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await traderApi.post("/api/trader-auth/request-otp/", { phone_number: phoneNumber });
      // Non-enumeration: backend always returns success if valid phone format
      navigate("/trader/verify-otp", { state: { phone_number: phoneNumber } });
    } catch (err: any) {
      setError(err.message || "Failed to request code.");
    } finally {
      setIsLoading(false);
    }
  };

  const verifyOtp = async (phoneNumber: string, code: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await traderApi.post("/api/trader-auth/verify-otp/", {
        phone_number: phoneNumber,
        code,
      });

      setAuth({
        accessToken: data.data.access,
        refreshToken: data.data.refresh,
        traderId: data.data.trader.trader_id,
        name: data.data.trader.name,
        phoneNumber: data.data.trader.phone_number,
      });

      navigate("/trader/dashboard");
    } catch (err: any) {
      setError(err.message || "Verification failed.");
      throw err; // For the component to catch and read remaining attempts if any
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    clearAuth();
    navigate("/trader/login", { replace: true });
  };

  return { requestOtp, verifyOtp, logout, isLoading, error, setError };
}
