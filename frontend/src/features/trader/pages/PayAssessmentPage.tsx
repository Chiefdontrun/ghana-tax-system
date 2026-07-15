import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import traderApi from "@/lib/traderApi";
import { formatMoney } from "@/lib/utils";

interface Assessment {
  assessment_id: string;
  tax_category: string;
  amount_due: number;
  amount_paid: number;
  status: string;
}

export default function PayAssessmentPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [network, setNetwork] = useState("mtn");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState("");
  const [paymentId, setPaymentId] = useState("");
  const [pollStatus, setPollStatus] = useState("");
  const [requiresOtp, setRequiresOtp] = useState(false);
  const [otp, setOtp] = useState("");
  const [otpDisplayText, setOtpDisplayText] = useState("");

  useEffect(() => {
    async function fetchAssessment() {
      try {
        const res = await traderApi.get(`/api/tax/assessments/?assessment_id=${id}`);
        // API returns a list, find the one
        const data = res.data.data?.data || res.data.data || [];
        const found = data.find((a: Assessment) => a.assessment_id === id);
        if (found) {
          setAssessment(found);
        } else {
          setError("Assessment not found.");
        }
      } catch (err: any) {
        setError("Failed to load assessment.");
      } finally {
        setLoading(false);
      }
    }
    fetchAssessment();
  }, [id]);

  useEffect(() => {
    if (!paymentId) return;
    
    let isSubscribed = true;
    
    const poll = async () => {
      try {
        const res = await traderApi.get(`/api/tax/payments/${paymentId}/status/`);
        if (!isSubscribed) return;
        
        const status = res.data.data.status;
        if (status === "SUCCESS") {
          setPollStatus("SUCCESS");
          setTimeout(() => navigate(`/trader/assessments/${id}/receipt`), 1500);
        } else if (status === "FAILED") {
          setPollStatus("FAILED");
          setError("Payment failed or was declined. Please try again.");
          setPaymentId(""); // Stop polling
          setPaying(false);
        } else if (status === "PENDING_AUTHORIZATION") {
          if (res.data.data.requires_otp && !requiresOtp) {
            setRequiresOtp(true);
            setOtpDisplayText(res.data.data.display_text || "Enter the OTP sent to your phone");
          }
          // Continue polling
          setTimeout(poll, 3000);
        }
      } catch (err) {
        if (!isSubscribed) return;
        setTimeout(poll, 3000); // Retry on temporary network error
      }
    };
    
    poll();
    
    return () => { isSubscribed = false; };
  }, [paymentId, requiresOtp, id, navigate]);

  const handleInitiate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assessment) return;
    
    setError("");
    setPaying(true);
    setPollStatus("");
    
    try {
      const payload: Record<string, any> = {
        assessment_id: assessment.assessment_id,
        momo_network: network,
      };
      if (phoneNumber) {
        payload.phone_number = phoneNumber;
      }
      
      const res = await traderApi.post("/api/tax/payments/initiate/", payload);
      setPaymentId(res.data.data.payment_id);
    } catch (err: any) {
      setError(err.message || "Failed to initiate payment");
      setPaying(false);
    }
  };

  const handleSubmitOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!paymentId || !otp) return;
    
    setError("");
    try {
      await traderApi.post(`/api/tax/payments/${paymentId}/submit-otp/`, { otp });
      setRequiresOtp(false);
      setOtp("");
      setOtpDisplayText("");
      // Polling loop will naturally pick up the change
    } catch (err: any) {
      setError(err.message || "Failed to submit OTP");
    }
  };

  if (loading) return <div className="text-center py-12 text-cu-muted">Loading...</div>;
  if (!assessment) return <div className="text-red-500 text-center py-12">{error}</div>;

  const balance = assessment.amount_due - assessment.amount_paid;

  if (balance <= 0) {
    return (
      <div className="max-w-md mx-auto bg-white rounded-xl border border-cu-border shadow-card-sm p-8 text-center">
        <h2 className="text-2xl font-bold text-cu-text mb-2">Already Paid</h2>
        <p className="text-cu-muted mb-6">This assessment has already been paid in full.</p>
        <button
          onClick={() => navigate("/trader/dashboard")}
          className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-cu-text rounded-lg transition-colors"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate("/trader/dashboard")}
          className="text-sm text-cu-muted hover:text-cu-text"
        >
          &larr; Back
        </button>
        <h1 className="text-xl font-semibold text-cu-text">Pay Tax Assessment</h1>
      </div>

      <div className="bg-white rounded-xl border border-cu-border shadow-card-sm overflow-hidden">
        <div className="p-6 border-b border-cu-border bg-slate-50">
          <h2 className="font-semibold text-cu-text">{assessment.tax_category.replace(/_/g, " ")}</h2>
          <div className="mt-4 flex justify-between items-end">
            <span className="text-sm text-cu-muted">Amount Due</span>
            <span className="text-3xl font-bold text-cu-text">GHS {formatMoney(balance)}</span>
          </div>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-4 bg-red-50 text-red-600 p-3 rounded-lg text-sm border border-red-200">
              {error}
            </div>
          )}

          {!paymentId ? (
            <form onSubmit={handleInitiate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-cu-text mb-1">Mobile Money Network</label>
                <select
                  value={network}
                  onChange={(e) => setNetwork(e.target.value)}
                  className="w-full px-3 py-2 border border-cu-border rounded-lg bg-white text-cu-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="mtn">MTN Mobile Money</option>
                  <option value="telecel">Telecel Cash (Vodafone)</option>
                  <option value="airteltigo">AT Money (AirtelTigo)</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-cu-text mb-1">
                  Phone Number (Optional)
                </label>
                <input
                  type="text"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="e.g. 0551234987"
                  className="w-full px-3 py-2 border border-cu-border rounded-lg bg-white text-cu-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-cu-muted mt-1">Leave blank to use your registered number.</p>
              </div>

              <button
                type="submit"
                disabled={paying}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors shadow-sm disabled:opacity-50"
              >
                {paying ? "Initiating..." : "Pay with Mobile Money"}
              </button>
            </form>
          ) : requiresOtp ? (
            <form onSubmit={handleSubmitOtp} className="space-y-4 text-center">
              <div className="text-amber-600 mb-2">
                <svg className="w-12 h-12 mx-auto animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-cu-text">{otpDisplayText}</h3>
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="Enter OTP"
                className="w-full text-center px-4 py-3 border border-cu-border rounded-lg bg-white text-cu-text focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg tracking-widest font-mono"
              />
              <button
                type="submit"
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors shadow-sm"
              >
                Submit OTP
              </button>
            </form>
          ) : (
            <div className="text-center space-y-4 py-4">
              {pollStatus === "SUCCESS" ? (
                <div className="text-emerald-600">
                  <svg className="w-16 h-16 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 className="text-xl font-bold">Payment Successful!</h3>
                  <p className="text-sm mt-2 text-cu-muted">Redirecting to receipt...</p>
                </div>
              ) : (
                <div className="text-blue-600">
                  <svg className="w-16 h-16 mx-auto mb-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <h3 className="text-lg font-medium text-cu-text">Awaiting Authorization</h3>
                  <p className="text-sm mt-2 text-cu-muted">Please approve the prompt on your phone.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
