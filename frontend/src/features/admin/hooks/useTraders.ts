import { useState, useEffect, useCallback, useRef } from "react";
import api from "@/lib/api";

export interface Trader {
  trader_id: string;
  tin_number: string;
  name: string;
  phone_number: string;
  channel: "web" | "ussd";
  business_type: string;
  region: string;
  district: string;
  market_name: string;
  created_at: string;
}

export interface TraderDetail extends Trader {
  business_name?: string;
  status?: string;
}

export interface TraderFilters {
  search?: string;
  channel?: string;
  business_type?: string;
  region?: string;
  district?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

interface TradersResponse {
  success: boolean;
  message: string;
  data: Trader[];
  pagination: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

interface TraderDetailResponse {
  success: boolean;
  message: string;
  data: TraderDetail;
}

interface UseTradersReturn {
  traders: Trader[];
  total: number;
  page: number;
  totalPages: number;
  isLoading: boolean;
  error: string | null;
  filters: TraderFilters;
  setFilters: (f: Partial<TraderFilters>) => void;
  resetFilters: () => void;
  refetch: () => void;
}

interface UseTraderDetailReturn {
  trader: TraderDetail | null;
  isLoading: boolean;
  error: string | null;
}

const DEFAULT_FILTERS: TraderFilters = {
  page: 1,
  page_size: 20,
};

export function useTraders(): UseTradersReturn {
  const [traders, setTraders] = useState<Trader[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFiltersState] = useState<TraderFilters>(DEFAULT_FILTERS);

  // Debounce timer ref for search
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Pending search value
  const pendingSearch = useRef<string | undefined>(undefined);

  const fetchTraders = useCallback(async (params: TraderFilters) => {
    setIsLoading(true);
    setError(null);
    try {
      // Build query string — omit empty values
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== "") qs.set(k, String(v));
      });
      const response = await api.get<TradersResponse>(`/api/traders?${qs.toString()}`);
      setTraders(response.data.data);
      setTotal(response.data.pagination.total);
      setTotalPages(response.data.pagination.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load traders.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Re-fetch whenever filters change
  useEffect(() => {
    fetchTraders(filters);
  }, [filters, fetchTraders]);

  const setFilters = (incoming: Partial<TraderFilters>) => {
    // If search is changing, debounce it; reset page for any filter change
    if ("search" in incoming) {
      pendingSearch.current = incoming.search;
      if (searchTimer.current) clearTimeout(searchTimer.current);
      searchTimer.current = setTimeout(() => {
        setFiltersState((prev) => ({
          ...prev,
          ...incoming,
          search: pendingSearch.current,
          page: 1,
        }));
      }, 300);
    } else {
      setFiltersState((prev) => ({ ...prev, ...incoming, page: 1 }));
    }
  };

  const resetFilters = () => setFiltersState(DEFAULT_FILTERS);

  return {
    traders,
    total,
    page: filters.page ?? 1,
    totalPages,
    isLoading,
    error,
    filters,
    setFilters,
    resetFilters,
    refetch: () => fetchTraders(filters),
  };
}

export function useTraderDetail(traderId: string): UseTraderDetailReturn {
  const [trader, setTrader] = useState<TraderDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!traderId) return;
    setIsLoading(true);
    setError(null);
    api
      .get<TraderDetailResponse>(`/api/traders/${traderId}`)
      .then((r) => setTrader(r.data.data))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load trader."))
      .finally(() => setIsLoading(false));
  }, [traderId]);

  return { trader, isLoading, error };
}
