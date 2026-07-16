import { useState } from "react";
import { Link } from "react-router-dom";
import { Alert, Button } from "@/components/ui";
import api from "@/lib/api";
import { useTaxExceptions, type TaxException } from "../hooks/useTax";

export default function TaxAssessmentExceptionsPage() {
  const [filters, setFilters] = useState({ status: "OPEN", exception_type: "" });
  const { items, total, isLoading, error, reload } = useTaxExceptions(filters);
  const [turnover, setTurnover] = useState<Record<string, string>>({});
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const resolveTurnover = async (ex: TaxException) => {
    const raw = turnover[ex.exception_id];
    const pesewas = Math.round(Number(raw) * 100);
    if (!raw || Number.isNaN(pesewas) || pesewas < 0) {
      setActionError("Enter declared turnover in GHS");
      return;
    }
    setBusy(ex.exception_id);
    setActionError(null);
    try {
      await api.post(`/api/tax/assessment-exceptions/${ex.exception_id}/resolve-turnover/`, {
        declared_turnover_pesewas: pesewas,
      });
      reload();
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : "Resolve failed");
    } finally {
      setBusy(null);
    }
  };

  const retry = async (ex: TaxException) => {
    setBusy(ex.exception_id);
    setActionError(null);
    try {
      await api.post(`/api/tax/assessment-exceptions/${ex.exception_id}/retry/`);
      reload();
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : "Retry failed — add a matching schedule first");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-cu-text">Assessment Exceptions</h1>
        <p className="text-sm text-cu-muted mt-0.5">
          Queue of NEEDS_TURNOVER / MISSING_SCHEDULE ({total} shown)
        </p>
      </div>

      {(error || actionError) && <Alert variant="error">{error || actionError}</Alert>}

      <div className="bg-white border border-cu-border rounded-lg p-4 flex flex-wrap gap-3">
        <div>
          <label className="block text-xs font-semibold text-cu-muted mb-1">Status</label>
          <select
            className="px-3 py-2 border rounded-md text-sm"
            value={filters.status}
            onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
          >
            <option value="OPEN">OPEN</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="">All</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-cu-muted mb-1">Type</label>
          <select
            className="px-3 py-2 border rounded-md text-sm"
            value={filters.exception_type}
            onChange={(e) => setFilters((f) => ({ ...f, exception_type: e.target.value }))}
          >
            <option value="">All</option>
            <option value="NEEDS_TURNOVER">NEEDS_TURNOVER</option>
            <option value="MISSING_SCHEDULE">MISSING_SCHEDULE</option>
          </select>
        </div>
      </div>

      <div className="bg-white border border-cu-border rounded-lg overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-cu-muted">
            <tr>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Business</th>
              <th className="px-3 py-2">Period</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-cu-muted">
                  Loading…
                </td>
              </tr>
            )}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-cu-muted">
                  No exceptions
                </td>
              </tr>
            )}
            {items.map((ex) => (
              <tr key={ex.exception_id} className="border-t border-cu-border align-top">
                <td className="px-3 py-2 font-medium">{ex.exception_type}</td>
                <td className="px-3 py-2">
                  {ex.business_type || "—"}
                  {ex.district ? ` · ${ex.district}` : ""}
                </td>
                <td className="px-3 py-2">{ex.period_label || "—"}</td>
                <td className="px-3 py-2">{ex.status}</td>
                <td className="px-3 py-2 space-y-2">
                  {ex.exception_type === "NEEDS_TURNOVER" && ex.status === "OPEN" && (
                    <div className="flex flex-wrap items-center gap-2">
                      <input
                        type="number"
                        step="0.01"
                        placeholder="Turnover GHS"
                        className="w-32 px-2 py-1 border rounded text-xs"
                        value={turnover[ex.exception_id] ?? ""}
                        onChange={(e) =>
                          setTurnover((t) => ({ ...t, [ex.exception_id]: e.target.value }))
                        }
                      />
                      <Button
                        type="button"
                        disabled={busy === ex.exception_id}
                        onClick={() => resolveTurnover(ex)}
                      >
                        Resolve
                      </Button>
                    </div>
                  )}
                  {ex.exception_type === "MISSING_SCHEDULE" && ex.status === "OPEN" && (
                    <div className="flex flex-wrap items-center gap-2">
                      <Link
                        to={`/admin/tax/rate-schedules?business_type=${encodeURIComponent(
                          ex.business_type || ""
                        )}&district=${encodeURIComponent(ex.district || "")}`}
                        className="text-xs text-cu-red font-semibold underline"
                      >
                        Add schedule
                      </Link>
                      <Button
                        type="button"
                        disabled={busy === ex.exception_id}
                        onClick={() => retry(ex)}
                      >
                        Retry
                      </Button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
