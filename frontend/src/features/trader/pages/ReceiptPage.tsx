import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import traderApi from "@/lib/traderApi";
import { formatMoney, formatDateTime } from "@/lib/utils";

interface Assessment {
  assessment_id: string;
  tax_category: string;
  amount_paid: number;
  updated_at: string;
}

export default function ReceiptPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAssessment() {
      try {
        const res = await traderApi.get(`/api/tax/assessments/?assessment_id=${id}`);
        const data = res.data.data?.data || res.data.data || [];
        const found = data.find((a: Assessment) => a.assessment_id === id);
        if (found) setAssessment(found);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchAssessment();
  }, [id]);

  if (loading) return <div className="text-center py-12 text-cu-muted">Loading receipt...</div>;
  if (!assessment) return <div className="text-center py-12 text-red-500">Receipt not found.</div>;

  return (
    <div className="max-w-md mx-auto space-y-6">
      <div className="flex items-center justify-between no-print">
        <button
          onClick={() => navigate("/trader/dashboard")}
          className="text-sm text-cu-muted hover:text-cu-text"
        >
          &larr; Back to Dashboard
        </button>
        <button
          onClick={() => window.print()}
          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-cu-text rounded text-sm font-medium transition-colors"
        >
          Print Receipt
        </button>
      </div>

      <div className="bg-white p-8 rounded-xl border border-cu-border shadow-card-sm print:shadow-none print:border-none print:p-0">
        <div className="text-center mb-8 border-b border-cu-border pb-6">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-cu-text">Payment Receipt</h1>
          <p className="text-cu-muted mt-1">Ghana Revenue Authority</p>
        </div>

        <div className="space-y-4 text-sm">
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-cu-muted">Date</span>
            <span className="font-medium text-cu-text">{formatDateTime(assessment.updated_at || new Date().toISOString())}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-cu-muted">Assessment ID</span>
            <span className="font-medium text-cu-text break-all ml-4 text-right">{assessment.assessment_id}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-cu-muted">Tax Category</span>
            <span className="font-medium text-cu-text">{assessment.tax_category.replace(/_/g, " ")}</span>
          </div>
          <div className="flex justify-between py-4 text-lg font-bold">
            <span className="text-cu-text">Total Paid</span>
            <span className="text-emerald-700">GHS {formatMoney(assessment.amount_paid)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
