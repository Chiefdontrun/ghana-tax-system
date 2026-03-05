import { Card } from "@/components/ui";
import BarChart from "@/components/charts/BarChart";
import LineChart from "@/components/charts/LineChart";
import DonutChart from "@/components/charts/DonutChart";
import StatsCard from "../components/StatsCard";
import { useReportSummary } from "../hooks/useReports";
import { formatBusinessType } from "@/lib/utils";
import { colors } from "@/styles/theme";
import type { Period } from "../hooks/useReports";

const PERIOD_LABELS: Record<Period, string> = { "7d": "7 Days", "30d": "30 Days", "all": "All Time" };

// ── Icon helpers ─────────────────────────────────────────────────────────────
function TotalIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

function WebIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
    </svg>
  );
}

function UssdIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
  );
}

function TrendIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  );
}

export default function DashboardPage() {
  const { data, isLoading, period, setPeriod } = useReportSummary();

  // Derive "today" registrations from daily_trend last entry
  const trend = data?.daily_trend;
  const todayCount = trend && trend.length > 0 ? trend[trend.length - 1].count : 0;

  // Build chart data
  const barData = data?.by_business_type.map((b) => ({
    type: formatBusinessType(b.type).slice(0, 10),
    count: b.count,
  })) ?? [];

  const donutData = data
    ? [
        { name: "Web", value: data.by_channel.web, color: colors.cuRed },
        { name: "USSD", value: data.by_channel.ussd, color: "#7C3AED" },
      ]
    : [];

  const lineData = data?.daily_trend.map((d) => ({
    date: d.date.slice(5), // "MM-DD"
    count: d.count,
  })) ?? [];

  // Top 5 districts from by_region
  const topRegions = data?.by_region.slice(0, 5) ?? [];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-cu-text">Dashboard</h1>
          <p className="text-sm text-cu-muted mt-0.5">Revenue Unit Registration Overview</p>
        </div>
        {/* Period filter */}
        <div className="flex items-center gap-1 bg-white border border-cu-border rounded-lg p-1">
          {(["7d", "30d", "all"] as Period[]).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1.5 rounded text-xs font-semibold transition-colors ${
                period === p
                  ? "bg-cu-red text-white"
                  : "text-cu-muted hover:text-cu-text"
              }`}
            >
              {PERIOD_LABELS[p]}
            </button>
          ))}
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatsCard label="Total Traders" value={data?.total_traders ?? 0} icon={<TotalIcon />} accent="red" isLoading={isLoading} />
        <StatsCard label="Today's Registrations" value={todayCount} icon={<TrendIcon />} accent="green" isLoading={isLoading} />
        <StatsCard label="Web Registrations" value={data?.by_channel.web ?? 0} icon={<WebIcon />} accent="blue" isLoading={isLoading} />
        <StatsCard label="USSD Registrations" value={data?.by_channel.ussd ?? 0} icon={<UssdIcon />} accent="purple" isLoading={isLoading} />
      </div>

      {/* Charts row */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Card headerTitle="Registrations by Business Type">
          <BarChart
            data={barData}
            xKey="type"
            bars={[{ dataKey: "count", name: "Traders", color: colors.cuRed }]}
            height={260}
            isLoading={isLoading}
          />
        </Card>
        <Card headerTitle="Web vs USSD Split">
          <DonutChart
            data={donutData}
            height={260}
            isLoading={isLoading}
            innerRadius={65}
            outerRadius={95}
          />
        </Card>
      </div>

      {/* Bottom row */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Card headerTitle="Daily Registrations (Last 30 Days)">
          <LineChart
            data={lineData}
            xKey="date"
            lines={[{ dataKey: "count", name: "Registrations", color: colors.cuRed }]}
            height={260}
            isLoading={isLoading}
          />
        </Card>

        <Card headerTitle="Top Regions by Registration">
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-cu-border">
                  <th className="px-3 py-2 text-left text-xs font-semibold text-cu-muted uppercase tracking-wide">Region</th>
                  <th className="px-3 py-2 text-right text-xs font-semibold text-cu-muted uppercase tracking-wide">Traders</th>
                  <th className="px-3 py-2 text-right text-xs font-semibold text-cu-muted uppercase tracking-wide">Share</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cu-border">
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i}>
                      <td colSpan={3} className="px-3 py-2.5">
                        <div className="h-4 bg-gray-100 rounded animate-pulse" />
                      </td>
                    </tr>
                  ))
                ) : topRegions.length === 0 ? (
                  <tr><td colSpan={3} className="px-3 py-4 text-center text-cu-muted text-xs">No data</td></tr>
                ) : (
                  topRegions.map((r) => (
                    <tr key={r.region} className="hover:bg-gray-50">
                      <td className="px-3 py-2.5 text-cu-text">{r.region}</td>
                      <td className="px-3 py-2.5 text-right tabular-nums font-semibold">{r.count.toLocaleString()}</td>
                      <td className="px-3 py-2.5 text-right text-cu-muted">
                        {data && data.total_traders > 0
                          ? `${Math.round((r.count / data.total_traders) * 100)}%`
                          : "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
