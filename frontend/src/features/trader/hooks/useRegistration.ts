import { useState } from "react";
import api from "@/lib/api";

export interface RegistrationPayload {
  name: string;
  phone_number: string;
  business_type: string;
  location: {
    region: string;
    district: string;
    market_name: string;
  };
}

export interface RegistrationResult {
  tin_number: string;
  trader_id: string;
  name: string;
  sms_status: string;
  phone_number: string;
}

export interface TinLookupResult {
  tin_number: string;
  name_masked: string;
  status: string;
}

interface UseRegistrationReturn {
  submit: (data: RegistrationPayload) => Promise<void>;
  lookupTin: (phone: string) => Promise<TinLookupResult | null>;
  result: RegistrationResult | null;
  tinLookupResult: TinLookupResult | null;
  isLoading: boolean;
  error: string | null;
  reset: () => void;
}

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export function useRegistration(): UseRegistrationReturn {
  const [result, setResult] = useState<RegistrationResult | null>(null);
  const [tinLookupResult, setTinLookupResult] = useState<TinLookupResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (data: RegistrationPayload) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.post<ApiResponse<RegistrationResult>>("/api/register", data);
      setResult({ ...response.data.data, phone_number: data.phone_number });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed. Please try again.");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const lookupTin = async (phone: string): Promise<TinLookupResult | null> => {
    setIsLoading(true);
    setError(null);
    setTinLookupResult(null);
    try {
      const response = await api.post<ApiResponse<TinLookupResult>>("/api/tin/lookup", {
        phone_number: phone,
      });
      setTinLookupResult(response.data.data);
      return response.data.data;
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number } };
      if (axiosErr?.response?.status === 404) {
        setError("No registration found for this phone number.");
      } else if (axiosErr?.response?.status === 429) {
        setError("Too many attempts. Please wait a moment and try again.");
      } else {
        setError(err instanceof Error ? err.message : "Lookup failed. Please try again.");
      }
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setResult(null);
    setTinLookupResult(null);
    setError(null);
    setIsLoading(false);
  };

  return { submit, lookupTin, result, tinLookupResult, isLoading, error, reset };
}
