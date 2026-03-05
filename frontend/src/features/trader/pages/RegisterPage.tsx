import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui";
import RegistrationForm from "../components/RegistrationForm";
import { useRegistration } from "../hooks/useRegistration";
import type { RegistrationPayload } from "../hooks/useRegistration";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { submit, result, isLoading, error } = useRegistration();

  // Navigate to success page once result is available
  useEffect(() => {
    if (result) {
      navigate("/register/success", {
        replace: true,
        state: {
          tin: result.tin_number,
          name: result.name,
          phone: result.phone_number,
        },
      });
    }
  }, [result, navigate]);

  const handleSubmit = async (payload: RegistrationPayload) => {
    try {
      await submit(payload);
    } catch {
      // error already set in hook — displayed by RegistrationForm via serverError prop
    }
  };

  return (
    <div className="max-w-xl mx-auto px-4 py-12">
      {/* Page header */}
      <div className="mb-8 text-center">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-cu-red/10 mb-3">
          <svg
            className="h-6 w-6 text-cu-red"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-cu-text">Register Your Business</h1>
        <p className="text-cu-muted text-sm mt-1">
          Complete the form below to receive your Tax Identification Number
        </p>
      </div>

      <Card>
        <RegistrationForm
          onSuccess={handleSubmit}
          isLoading={isLoading}
          serverError={error}
        />
      </Card>

      <p className="text-center text-xs text-cu-muted mt-6">
        Already registered?{" "}
        <a href="/check-tin" className="text-cu-red hover:underline font-medium">
          Look up your TIN
        </a>
      </p>
    </div>
  );
}
