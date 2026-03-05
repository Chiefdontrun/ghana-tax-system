import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";

export type Period = "7d" | "30d" | "all";

export interface ByChannel {
  web: number;
  ussd: number;
}

export interface ByType {
  type: string;
  count: number;
}

export interface ByRegion {
  region: string;
  count: number;
}

export interface DailyTrend {
  date: string;
  count: number;
}

export interface ReportSummaryData {
  total_traders: number;
  period: string;
  by_channel: ByChannel;
  by_business_type: ByType[];
  by_region: ByRegion[];
  daily_trend: DailyTrend[];
  generated_at: string;
}

export interface AuditLog {
  log_id: string;
  action: string;
  actor_id: string;
  actor_role: string;
  entity_id?: string;
  entity_type?: string;
  channel?: string;
  ip_address?: string;
  created_at: string;
  meta?: Record<string, unknown>;
}

interface AuditLogsResponse {
  success: boolean;
  message: string;
  data: AuditLog[];
  pagination: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

interface ReportSummaryResponse {
  success: boolean;
  message: string;
  data: ReportSummaryData;
}

export interface AuditFilters {
  action?: string;
  actor_id?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

// ── Summary hook ──────────────────────────────────────────────────────────────
interface UseReportSummaryReturn {
  data: ReportSummaryData | null;
  isLoading: boolean;
  error: string | null;
  period: Period;
  setPeriod: (p: Period) => void;
  refetch: () => void;
}

export function useReportSummary(): UseReportSummaryReturn {
  const [data, setData] = useState<ReportSummaryData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<Period>("30d");

  const fetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<ReportSummaryResponse>(
        `/api/reports/summary?period=${period}`
      );
      setData(response.data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load report.");
    } finally {
      setIsLoading(false);
    }
  }, [period]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, isLoading, error, period, setPeriod, refetch: fetch };
}

// ── CSV export ────────────────────────────────────────────────────────────────
export function useExportCsv() {
  const [isExporting, setIsExporting] = useState(false);

  const exportCsv = async (filters: Record<string, string> = {}) => {
    setIsExporting(true);
    try {
      const qs = new URLSearchParams({ format: "csv", ...filters });
      const response = await api.get(`/api/reports/export?${qs.toString()}`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data as BlobPart]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `traders-export-${new Date().toISOString().slice(0, 10)}.csv`
      );
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed:", err);
    } finally {
      setIsExporting(false);
    }
  };

  return { exportCsv, isExporting };
}

// ── Audit logs hook ───────────────────────────────────────────────────────────
interface UseAuditLogsReturn {
  logs: AuditLog[];
  total: number;
  page: number;
  totalPages: number;
  isLoading: boolean;
  error: string | null;
  filters: AuditFilters;
  setFilters: (f: Partial<AuditFilters>) => void;
}

export function useAuditLogs(): UseAuditLogsReturn {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFiltersState] = useState<AuditFilters>({ page: 1, page_size: 20 });

  const fetchLogs = useCallback(async (params: AuditFilters) => {
    setIsLoading(true);
    setError(null);
    try {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== "") qs.set(k, String(v));
      });
      const response = await api.get<AuditLogsResponse>(`/api/audit-logs?${qs.toString()}`);
      setLogs(response.data.data);
      setTotal(response.data.pagination.total);
      setTotalPages(response.data.pagination.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit logs.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs(filters);
  }, [filters, fetchLogs]);

  const setFilters = (incoming: Partial<AuditFilters>) => {
    setFiltersState((prev) => ({ ...prev, ...incoming, page: 1 }));
  };

  return {
    logs,
    total,
    page: filters.page ?? 1,
    totalPages,
    isLoading,
    error,
    filters,
    setFilters,
  };
}
