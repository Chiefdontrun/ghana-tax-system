import { formatBusinessType } from "@/lib/utils";
import { Spinner } from "@/components/ui";
import type { ReportSummaryData } from "../hooks/useReports";

interface ReportSummaryProps {
  data: ReportSummaryData | null;
  isLoading: boolean;
}

function SummaryRow({ label, value, bold }: { label: string; value: string | number; bold?: boolean }) {
  return (
    <tr className={bold ? "bg-gray-50 font-semibold" : "hover:bg-gray-50"}>
      <td className="px-4 py-2.5 text-sm text-cu-text border-b border-cu-border">{label}</td>
      <td className="px-4 py-2.5 text-sm text-cu-text text-right tabular-nums border-b border-cu-border">
        {typeof value === "number" ? value.toLocaleString() : value}
      </td>
    </tr>
  );
}

function formatCount(value: number | string | null | undefined) {
  const amount = Number(value ?? 0);
  return Number.isFinite(amount) ? amount.toLocaleString() : "0";
}

export default function ReportSummary({ data, isLoading }: ReportSummaryProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!data) return null;

  const totalTraders = Number(data.total_traders ?? 0);
  const webCount = Number(data.by_channel?.web ?? 0);
  const ussdCount = Number(data.by_channel?.ussd ?? 0);
  const webPct = totalTraders > 0
    ? Math.round((webCount / totalTraders) * 100)
    : 0;
  const ussdPct = totalTraders > 0
    ? Math.round((ussdCount / totalTraders) * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* Totals table */}
      <div className="rounded-lg border border-cu-border overflow-hidden">
        <div className="bg-cu-red px-4 py-2.5">
          <h3 className="text-sm font-semibold text-white">Registration Summary</h3>
        </div>
        <table className="min-w-full">
          <tbody>
            <SummaryRow label="Total Registered Traders" value={totalTraders} bold />
            <SummaryRow label="Web Registrations" value={`${formatCount(webCount)} (${webPct}%)`} />
            <SummaryRow label="USSD Registrations" value={`${formatCount(ussdCount)} (${ussdPct}%)`} />
          </tbody>
        </table>
      </div>

      {/* By region */}
      {data.by_region.length > 0 && (
        <div className="rounded-lg border border-cu-border overflow-hidden">
          <div className="bg-gray-50 border-b border-cu-border px-4 py-2.5">
            <h3 className="text-sm font-semibold text-cu-text">Registrations by Region</h3>
          </div>
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-cu-border">
                <th className="px-4 py-2 text-xs font-semibold text-cu-muted uppercase tracking-wide text-left">Region</th>
                <th className="px-4 py-2 text-xs font-semibold text-cu-muted uppercase tracking-wide text-right">Count</th>
                <th className="px-4 py-2 text-xs font-semibold text-cu-muted uppercase tracking-wide text-right">Share</th>
              </tr>
            </thead>
            <tbody>
              {data.by_region.map((r) => (
                <tr key={r.region} className="border-b border-cu-border hover:bg-gray-50">
                  <td className="px-4 py-2.5 text-sm text-cu-text">{r.region}</td>
                  <td className="px-4 py-2.5 text-sm text-right tabular-nums">{formatCount(r.count)}</td>
                  <td className="px-4 py-2.5 text-sm text-right text-cu-muted">
                    {totalTraders > 0
                      ? `${Math.round((Number(r.count ?? 0) / totalTraders) * 100)}%`
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* By business type */}
      {data.by_business_type.length > 0 && (
        <div className="rounded-lg border border-cu-border overflow-hidden">
          <div className="bg-gray-50 border-b border-cu-border px-4 py-2.5">
            <h3 className="text-sm font-semibold text-cu-text">Registrations by Business Type</h3>
          </div>
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-cu-border">
                <th className="px-4 py-2 text-xs font-semibold text-cu-muted uppercase tracking-wide text-left">Business Type</th>
                <th className="px-4 py-2 text-xs font-semibold text-cu-muted uppercase tracking-wide text-right">Count</th>
              </tr>
            </thead>
            <tbody>
              {data.by_business_type.map((b) => (
                <tr key={b.type} className="border-b border-cu-border hover:bg-gray-50">
                  <td className="px-4 py-2.5 text-sm text-cu-text">{formatBusinessType(b.type)}</td>
                  <td className="px-4 py-2.5 text-sm text-right tabular-nums">{formatCount(b.count)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-cu-muted text-right">
        Generated: {data.generated_at ? new Date(data.generated_at).toLocaleString("en-GH") : "Not available"}
      </p>
    </div>
  );
}
