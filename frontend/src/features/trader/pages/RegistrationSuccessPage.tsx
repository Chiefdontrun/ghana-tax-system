import { useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import TinDisplay from "../components/TinDisplay";

interface SuccessState {
  tin: string;
  name: string;
  phone: string;
}

export default function RegistrationSuccessPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as SuccessState | null;

  // Guard: if navigated here directly without TIN data, redirect to /register
  useEffect(() => {
    if (!state?.tin) {
      navigate("/register", { replace: true });
    }
  }, [state, navigate]);

  if (!state?.tin) return null;

  const { tin, name, phone } = state;

  return (
    <div className="max-w-xl mx-auto px-4 py-12">
      {/* Success header */}
      <div className="flex flex-col items-center text-center mb-8 gap-3">
        <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center">
          <svg
            className="h-9 w-9 text-green-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-cu-text">Registration Successful!</h1>
        <p className="text-cu-muted text-sm">
          Welcome, <span className="font-semibold text-cu-text">{name}</span>. Your business
          has been registered with the District Assembly Revenue Unit.
        </p>
      </div>

      {/* TIN display */}
      <TinDisplay tin={tin} />

      {/* Instructions */}
      <div className="mt-6 rounded-lg bg-amber-50 border border-amber-200 px-5 py-4 text-sm text-amber-800">
        <div className="flex gap-2">
          <svg className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p>
            <strong>Important:</strong> Screenshot or write down your TIN number. You will need
            it for all transactions with the Revenue Unit.
          </p>
        </div>
      </div>

      {/* SMS notice */}
      {phone && (
        <div className="mt-4 rounded-lg bg-blue-50 border border-blue-200 px-5 py-3 text-sm text-blue-800 flex gap-2">
          <svg className="h-5 w-5 text-blue-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <p>
            An SMS confirmation has been sent to{" "}
            <span className="font-semibold">{phone}</span>.
          </p>
        </div>
      )}

      {/* Action buttons */}
      <div className="mt-8 flex flex-col sm:flex-row gap-3">
        <Link
          to="/register"
          className="flex-1 inline-flex items-center justify-center gap-2 rounded-md border border-cu-border bg-white text-cu-text font-semibold px-5 py-3 text-sm hover:bg-gray-50 transition-colors"
        >
          Register Another Business
        </Link>
        <Link
          to="/check-tin"
          className="flex-1 inline-flex items-center justify-center gap-2 rounded-md bg-cu-red text-white font-semibold px-5 py-3 text-sm hover:bg-cu-red-dark transition-colors"
        >
          Check Your TIN
        </Link>
      </div>
    </div>
  );
}
