import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTraderAuthStore } from "@/store/traderAuthStore";
import traderApi from "@/lib/traderApi";
import { formatMoney } from "@/lib/utils";

interface Business {
  tin: string;
  name: string;
  business_type: string;
  status: string;
}

interface Assessment {
  assessment_id: string;
  tax_category: string;
  period_label: string;
  amount_due: number;
  amount_paid: number;
  status: string;
  due_date: string;
}

export default function DashboardPage() {
  const { name, phoneNumber } = useTraderAuthStore();
  const navigate = useNavigate();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchData() {
      try {
        const [bizRes, assessRes] = await Promise.all([
          traderApi.get("/api/my-businesses/"),
          traderApi.get("/api/tax/assessments/")
        ]);
        setBusinesses(bizRes.data.data || []);
        // The API might paginate assessments, handle typical DRF response
        setAssessments(assessRes.data.data?.data || assessRes.data.data || []);
      } catch (err: any) {
        setError(err.message || "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return <div className="text-center py-12 text-cu-muted">Loading your dashboard...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 text-red-600 p-4 rounded-xl border border-red-200">
        {error}
      </div>
    );
  }

  const outstanding = assessments.filter(a => ["PENDING", "PARTIAL", "OVERDUE"].includes(a.status));
  const paid = assessments.filter(a => a.status === "PAID");

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-cu-text tracking-tight">Trader Dashboard</h1>
        <div className="bg-white px-4 py-2 rounded-lg border border-cu-border shadow-sm text-sm">
          <span className="text-cu-muted">Logged in as</span> <strong className="text-cu-text">{name || phoneNumber}</strong>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-cu-border shadow-card-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-cu-border bg-slate-50">
          <h2 className="text-lg font-semibold text-cu-text">My Businesses</h2>
        </div>
        <div className="p-6">
          {businesses.length === 0 ? (
            <p className="text-cu-muted">No businesses registered to this account.</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {businesses.map((biz) => (
                <div key={biz.tin} className="p-4 rounded-lg border border-cu-border bg-slate-50/50">
                  <h3 className="font-semibold text-cu-text">{biz.name}</h3>
                  <div className="mt-2 text-sm text-cu-muted space-y-1">
                    <p>TIN: <span className="text-cu-text font-medium">{biz.tin}</span></p>
                    <p>Type: {biz.business_type}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="space-y-6">
        <h2 className="text-2xl font-semibold text-cu-text">Tax Assessments</h2>

        <div className="bg-white rounded-xl border border-cu-border shadow-card-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-cu-border bg-amber-50/50">
            <h3 className="font-semibold text-amber-900">Action Required</h3>
          </div>
          <div className="p-6">
            {outstanding.length === 0 ? (
              <p className="text-cu-muted">You have no outstanding assessments.</p>
            ) : (
              <div className="space-y-4">
                {outstanding.map((a) => (
                  <div key={a.assessment_id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-lg border border-amber-200 bg-amber-50/30">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-cu-text">{a.tax_category.replace(/_/g, " ")}</h4>
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                          {a.status}
                        </span>
                      </div>
                      <p className="text-sm text-cu-muted mt-1">Period: {a.period_label} • Due: {a.due_date}</p>
                    </div>
                    <div className="mt-4 sm:mt-0 flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-lg font-bold text-amber-700">
                          GHS {formatMoney(a.amount_due - a.amount_paid)}
                        </div>
                        <div className="text-xs text-cu-muted">Balance Due</div>
                      </div>
                      <button
                        onClick={() => navigate(`/trader/assessments/${a.assessment_id}/pay`)}
                        className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-medium transition-colors shadow-sm"
                      >
                        Pay Now
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {paid.length > 0 && (
          <div className="bg-white rounded-xl border border-cu-border shadow-card-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-cu-border bg-emerald-50/50">
              <h3 className="font-semibold text-emerald-900">Payment History</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {paid.map((a) => (
                  <div key={a.assessment_id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-lg border border-emerald-200 bg-emerald-50/30">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-cu-text">{a.tax_category.replace(/_/g, " ")}</h4>
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800">
                          {a.status}
                        </span>
                      </div>
                      <p className="text-sm text-cu-muted mt-1">Period: {a.period_label}</p>
                    </div>
                    <div className="mt-4 sm:mt-0 text-right">
                      <div className="text-lg font-bold text-emerald-700">
                        GHS {formatMoney(a.amount_paid)}
                      </div>
                      <div className="text-xs text-cu-muted">Paid in Full</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
