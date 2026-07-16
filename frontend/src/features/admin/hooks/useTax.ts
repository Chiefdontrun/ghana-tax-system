import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";

export interface RateSchedule {
  schedule_id: string;
  tax_category: string;
  business_type: string;
  region?: string | null;
  district?: string | null;
  rate_type: "FIXED" | "PERCENTAGE_TURNOVER";
  fixed_amount?: number | null;
  percentage_rate?: number | null;
  min_amount?: number | null;
  max_amount?: number | null;
  period?: string;
  effective_year?: number;
  is_active?: boolean;
}

export interface TaxAssessment {
  assessment_id: string;
  trader_id?: string;
  tax_category?: string;
  period_label?: string;
  business_type?: string;
  region?: string;
  district?: string;
  amount_due?: number;
  amount_paid?: number;
  status?: string;
  due_date?: string;
  payments?: TaxPayment[];
}

export interface TaxPayment {
  payment_id: string;
  assessment_id?: string;
  amount_pesewas?: number;
  amount?: number;
  channel?: string;
  momo_network?: string;
  provider?: string;
  status?: string;
  created_at?: string;
}

export interface TaxException {
  exception_id: string;
  exception_type: "NEEDS_TURNOVER" | "MISSING_SCHEDULE" | string;
  status: string;
  business_id?: string;
  business_type?: string;
  district?: string;
  tax_category?: string;
  period_label?: string;
  created_at?: string;
}

export interface TaxKpis {
  total_assessed_ghs: number;
  total_collected_ghs: number;
  collection_rate_pct: number;
  overdue_count: number;
  assessment_count?: number;
  by_business_type?: Array<{
    business_type: string;
    total_assessed_ghs: number;
    total_collected_ghs: number;
    collection_rate_pct: number;
  }>;
}

function ghs(pesewas?: number) {
  return ((pesewas ?? 0) / 100).toFixed(2);
}

export { ghs };

export function useRateSchedules(filters: Record<string, string | number | undefined>) {
  const [items, setItems] = useState<RateSchedule[]>([]);
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v !== undefined && v !== "")
      );
      const { data } = await api.get("/api/tax/rate-schedules/", { params });
      setItems(data.data ?? []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load schedules");
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(filters)]);

  useEffect(() => {
    load();
  }, [load]);

  return { items, isLoading, error, reload: load, setItems };
}

export function useTaxAssessments(filters: Record<string, string | number | undefined>) {
  const [items, setItems] = useState<TaxAssessment[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        page_size: 20,
        ...Object.fromEntries(
          Object.entries(filters).filter(([, v]) => v !== undefined && v !== "")
        ),
      };
      const { data } = await api.get("/api/tax/assessments/", { params });
      setItems(data.data ?? []);
      setTotal(data.pagination?.total ?? data.meta?.total ?? 0);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load assessments");
    } finally {
      setLoading(false);
    }
  }, [page, JSON.stringify(filters)]);

  useEffect(() => {
    load();
  }, [load]);

  return { items, total, page, setPage, isLoading, error, reload: load };
}

export function useTaxExceptions(filters: Record<string, string | undefined>) {
  const [items, setItems] = useState<TaxException[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        status: filters.status || "OPEN",
        ...Object.fromEntries(
          Object.entries(filters).filter(([k, v]) => k !== "status" && v)
        ),
      };
      const { data } = await api.get("/api/tax/assessment-exceptions/", { params });
      setItems(data.data ?? []);
      setTotal(data.pagination?.total ?? data.meta?.total ?? 0);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load exceptions");
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(filters)]);

  useEffect(() => {
    load();
  }, [load]);

  return { items, total, isLoading, error, reload: load };
}

export function useTaxKpis(periodLabel?: string) {
  const [tax, setTax] = useState<TaxKpis | null>(null);
  const [isLoading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const { data } = await api.get("/api/reports/summary/", {
          params: { period: "all", period_label: periodLabel || undefined },
        });
        if (!cancelled) setTax(data.data?.tax ?? null);
      } catch {
        if (!cancelled) setTax(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [periodLabel]);

  return { tax, isLoading };
}
