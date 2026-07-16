import { Fragment, useState } from "react";
import { Alert } from "@/components/ui";
import api from "@/lib/api";
import { ghs, useTaxAssessments, type TaxAssessment, type TaxPayment } from "../hooks/useTax";

export default function TaxPaymentsPage() {
  const [filters, setFilters] = useState<Record<string, string>>({});
  const { items, total, page, setPage, isLoading, error, reload } = useTaxAssessments(filters);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [payments, setPayments] = useState<TaxPayment[]>([]);
  const [detailError, setDetailError] = useState<string | null>(null);

  const loadPayments = async (a: TaxAssessment) => {
    if (expanded === a.assessment_id) {
      setExpanded(null);
      return;
    }
    setDetailError(null);
    try {
      const { data } = await api.get(`/api/tax/assessments/${a.assessment_id}/`);
      setPayments(data.data?.payments ?? []);
      setExpanded(a.assessment_id);
    } catch (e: unknown) {
      setDetailError(e instanceof Error ? e.message : "Failed to load payments");
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-cu-text">Tax Assessments & Payments</h1>
        <p className="text-sm text-cu-muted mt-0.5">
          {isLoading ? "Loading…" : `${total.toLocaleString()} assessment(s)`}
        </p>
      </div>

      {(error || detailError) && <Alert variant="error">{error || detailError}</Alert>}

      <div className="bg-white border border-cu-border rounded-lg p-4 grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          ["status", "Status"],
          ["business_type", "Business type"],
          ["region", "Region"],
          ["district", "District"],
          ["period_label", "Period label"],
        ].map(([key, label]) => (
          <div key={key}>
            <label className="block text-xs font-semibold text-cu-muted mb-1">{label}</label>
            <input
              className="w-full px-3 py-2 rounded-md border border-cu-border text-sm"
              value={filters[key] ?? ""}
              onChange={(e) => {
                setPage(1);
                setFilters((f) => ({ ...f, [key]: e.target.value }));
              }}
              placeholder="Any"
            />
          </div>
        ))}
        <div className="flex items-end">
          <button
            type="button"
            className="text-sm text-cu-red font-medium"
            onClick={() => {
              setFilters({});
              setPage(1);
              reload();
            }}
          >
            Reset
          </button>
        </div>
      </div>

      <div className="bg-white border border-cu-border rounded-lg overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs text-cu-muted">
            <tr>
              <th className="px-3 py-2">Period</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Location</th>
              <th className="px-3 py-2">Due (GHS)</th>
              <th className="px-3 py-2">Paid (GHS)</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-cu-muted">
                  Loading…
                </td>
              </tr>
            )}
            {items.map((a) => (
              <Fragment key={a.assessment_id}>
                <tr className="border-t border-cu-border">
                  <td className="px-3 py-2">{a.period_label}</td>
                  <td className="px-3 py-2">{a.business_type || a.tax_category}</td>
                  <td className="px-3 py-2">
                    {[a.region, a.district].filter(Boolean).join(" / ")}
                  </td>
                  <td className="px-3 py-2">{ghs(a.amount_due)}</td>
                  <td className="px-3 py-2">{ghs(a.amount_paid)}</td>
                  <td className="px-3 py-2 font-medium">{a.status}</td>
                  <td className="px-3 py-2">
                    <button
                      type="button"
                      className="text-cu-red text-xs font-semibold"
                      onClick={() => loadPayments(a)}
                    >
                      {expanded === a.assessment_id ? "Hide" : "Payments"}
                    </button>
                  </td>
                </tr>
                {expanded === a.assessment_id && (
                  <tr className="bg-gray-50">
                    <td colSpan={7} className="px-4 py-3">
                      {payments.length === 0 ? (
                        <p className="text-xs text-cu-muted">No payment attempts</p>
                      ) : (
                        <ul className="text-xs space-y-1">
                          {payments.map((p) => (
                            <li key={p.payment_id}>
                              {p.payment_id.slice(0, 8)}… · {p.channel}/{p.momo_network} ·{" "}
                              {p.provider} · {p.status} · GHS{" "}
                              {ghs(p.amount_pesewas ?? p.amount)}
                            </li>
                          ))}
                        </ul>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-sm">
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          className="text-cu-red disabled:opacity-40"
        >
          Previous
        </button>
        <span className="text-cu-muted">Page {page}</span>
        <button
          type="button"
          disabled={items.length < 20}
          onClick={() => setPage((p) => p + 1)}
          className="text-cu-red disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>
  );
}
