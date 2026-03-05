import { useParams, Link } from "react-router-dom";
import { Card, Badge, Spinner, Alert } from "@/components/ui";
import { formatDateTime, formatBusinessType } from "@/lib/utils";
import { useTraderDetail } from "../hooks/useTraders";

function DetailRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-start gap-1 py-3 border-b border-cu-border last:border-0">
      <dt className="text-xs font-semibold text-cu-muted uppercase tracking-wide w-44 shrink-0">{label}</dt>
      <dd className="text-sm text-cu-text">{value ?? "—"}</dd>
    </div>
  );
}

export default function TraderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { trader, isLoading, error } = useTraderDetail(id ?? "");

  return (
    <div className="max-w-3xl space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-cu-muted" aria-label="Breadcrumb">
        <Link to="/admin/traders" className="hover:text-cu-red transition-colors">
          Traders
        </Link>
        <span aria-hidden>›</span>
        <span className="text-cu-text font-medium">
          {isLoading ? "Loading…" : (trader?.name ?? "Detail")}
        </span>
      </nav>

      {error && <Alert variant="error">{error}</Alert>}

      {isLoading ? (
        <div className="flex items-center justify-center py-24">
          <Spinner size="lg" />
        </div>
      ) : trader ? (
        <>
          {/* Profile card */}
          <Card>
            <div className="flex items-start gap-4">
              <div className="h-12 w-12 rounded-full bg-cu-red/10 text-cu-red flex items-center justify-center font-bold text-lg shrink-0">
                {trader.name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 flex-wrap">
                  <h1 className="text-xl font-bold text-cu-text">{trader.name}</h1>
                  <Badge variant={trader.channel === "web" ? "web" : "ussd"}>
                    {trader.channel.toUpperCase()}
                  </Badge>
                  <Badge variant="active">Active</Badge>
                </div>
                <p className="text-3xl font-bold font-mono text-cu-red mt-2 tracking-widest">
                  {trader.tin_number}
                </p>
                <p className="text-xs text-cu-muted mt-1">Tax Identification Number</p>
              </div>
            </div>
          </Card>

          {/* Personal info */}
          <Card headerTitle="Personal Information">
            <dl>
              <DetailRow label="Full Name" value={trader.name} />
              <DetailRow label="Phone Number" value={trader.phone_number} />
              <DetailRow label="TIN Number" value={trader.tin_number} />
            </dl>
          </Card>

          {/* Business info */}
          <Card headerTitle="Business Information">
            <dl>
              <DetailRow label="Business Type" value={formatBusinessType(trader.business_type)} />
              {trader.business_name && (
                <DetailRow label="Business Name" value={trader.business_name} />
              )}
              <DetailRow label="Region" value={trader.region} />
              <DetailRow label="District" value={trader.district} />
              <DetailRow label="Market / Community" value={trader.market_name} />
            </dl>
          </Card>

          {/* Registration info */}
          <Card headerTitle="Registration Details">
            <dl>
              <DetailRow label="Registration Channel" value={trader.channel.toUpperCase()} />
              <DetailRow label="Registered At" value={formatDateTime(trader.created_at)} />
              <DetailRow label="Trader ID" value={trader.trader_id} />
            </dl>
          </Card>

          {/* Back button */}
          <Link
            to="/admin/traders"
            className="inline-flex items-center gap-2 text-sm font-medium text-cu-muted hover:text-cu-red transition-colors"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Back to Traders
          </Link>
        </>
      ) : (
        <Alert variant="error">Trader not found.</Alert>
      )}
    </div>
  );
}
