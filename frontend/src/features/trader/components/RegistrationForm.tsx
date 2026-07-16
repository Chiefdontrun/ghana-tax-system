import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button, Input, Select, Alert } from "@/components/ui";
import type { RegistrationPayload } from "../hooks/useRegistration";

// ── Zod schema ────────────────────────────────────────────────────────────────
const ghanaPhoneRegex = /^(\+233|0|233)[2-9][0-9]{8}$/;

const INCOME_BRACKETS = [
  { value: "BRACKET_1", label: "GHC 100 – 400" },
  { value: "BRACKET_2", label: "GHC 401 – 1,000" },
  { value: "BRACKET_3", label: "GHC 1,001 – 3,000" },
  { value: "BRACKET_4", label: "GHC 3,001+" },
] as const;

const schema = z.object({
  name: z.string().min(3, "Full name must be at least 3 characters").max(80, "Name too long"),
  phone_number: z
    .string()
    .regex(ghanaPhoneRegex, "Enter a valid Ghana phone number (e.g. 0244123456)"),
  business_type: z.string().min(1, "Select a business type"),
  region: z.string().min(1, "Select a region"),
  district: z.string().min(2, "Enter your district").max(80, "District name too long"),
  market_name: z.string().min(2, "Enter market or community name").max(80, "Name too long"),
  income_bracket: z.enum(["BRACKET_1", "BRACKET_2", "BRACKET_3", "BRACKET_4"], {
    required_error: "Select your monthly income bracket",
    invalid_type_error: "Select your monthly income bracket",
  }),
});

type FormValues = z.infer<typeof schema>;

// Hawker first (presentation order only).
const BUSINESS_TYPES = [
  { value: "hawker", label: "Hawker" },
  { value: "food_vendor", label: "Food Vendor" },
  { value: "clothing", label: "Clothing" },
  { value: "electronics", label: "Electronics" },
  { value: "services", label: "Services" },
  { value: "agriculture", label: "Agriculture" },
  { value: "wholesale", label: "Wholesale" },
  { value: "retail", label: "Retail" },
  { value: "artisan", label: "Artisan" },
  { value: "other", label: "Other" },
];

const REGIONS = [
  { value: "Greater Accra", label: "Greater Accra" },
  { value: "Ashanti", label: "Ashanti" },
  { value: "Western", label: "Western" },
  { value: "Northern", label: "Northern" },
  { value: "Eastern", label: "Eastern" },
  { value: "Volta", label: "Volta" },
  { value: "Other", label: "Other" },
];

// ── Step indicator ────────────────────────────────────────────────────────────
function StepIndicator({ step }: { step: 1 | 2 | 3 }) {
  const steps = ["Personal Info", "Business Info", "Income Bracket"];
  return (
    <div className="flex items-center gap-0 mb-8">
      {steps.map((label, i) => {
        const num = i + 1;
        const isActive = num === step;
        const isDone = num < step;
        return (
          <div key={label} className="flex items-center flex-1 last:flex-none">
            <div className="flex flex-col items-center gap-1">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-colors ${
                  isActive
                    ? "bg-cu-red border-cu-red text-white"
                    : isDone
                    ? "bg-cu-red border-cu-red text-white"
                    : "bg-white border-cu-border text-cu-muted"
                }`}
              >
                {isDone ? (
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  num
                )}
              </div>
              <span className={`text-xs font-medium whitespace-nowrap ${isActive ? "text-cu-red" : "text-cu-muted"}`}>
                {label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={`flex-1 h-0.5 mx-2 mb-5 ${isDone ? "bg-cu-red" : "bg-cu-border"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
interface RegistrationFormProps {
  onSuccess: (payload: RegistrationPayload) => void;
  isLoading: boolean;
  serverError: string | null;
}

export default function RegistrationForm({
  onSuccess,
  isLoading,
  serverError,
}: RegistrationFormProps) {
  const [step, setStep] = useState<1 | 2 | 3>(1);

  const {
    register,
    handleSubmit,
    trigger,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    mode: "onTouched",
  });

  const handleNextFromPersonal = async () => {
    const valid = await trigger(["name", "phone_number"]);
    if (valid) setStep(2);
  };

  const handleNextFromBusiness = async () => {
    const valid = await trigger(["business_type", "region", "district", "market_name"]);
    if (valid) setStep(3);
  };

  const onSubmit = (values: FormValues) => {
    onSuccess({
      name: values.name,
      phone_number: values.phone_number,
      business_type: values.business_type,
      income_bracket: values.income_bracket,
      location: {
        region: values.region,
        district: values.district,
        market_name: values.market_name,
      },
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <StepIndicator step={step} />

      {serverError && (
        <Alert variant="error" className="mb-6">
          {serverError}
        </Alert>
      )}

      {/* ── Step 1: Personal Info ── */}
      {step === 1 && (
        <div className="space-y-5">
          <Input
            label="Full Name"
            placeholder="e.g. Kofi Mensah"
            required
            error={errors.name?.message}
            {...register("name")}
          />
          <Input
            label="Phone Number"
            placeholder="e.g. 0244123456 or +233244123456"
            type="tel"
            required
            helperText="Ghana phone number — used to retrieve your TIN later"
            error={errors.phone_number?.message}
            {...register("phone_number")}
          />
          <Button
            type="button"
            variant="primary"
            size="lg"
            fullWidth
            onClick={handleNextFromPersonal}
          >
            Next: Business Info →
          </Button>
        </div>
      )}

      {/* ── Step 2: Business Info ── */}
      {step === 2 && (
        <div className="space-y-5">
          <Select
            label="Business Type"
            required
            placeholder="Select business type"
            options={BUSINESS_TYPES}
            error={errors.business_type?.message}
            {...register("business_type")}
          />
          <Select
            label="Region"
            required
            placeholder="Select region"
            options={REGIONS}
            error={errors.region?.message}
            {...register("region")}
          />
          <Input
            label="District"
            placeholder="e.g. Accra Metropolitan"
            required
            error={errors.district?.message}
            {...register("district")}
          />
          <Input
            label="Market / Community Name"
            placeholder="e.g. Makola Market"
            required
            error={errors.market_name?.message}
            {...register("market_name")}
          />
          <div className="flex gap-3 pt-1">
            <Button
              type="button"
              variant="secondary"
              size="lg"
              className="flex-1"
              onClick={() => setStep(1)}
              disabled={isLoading}
            >
              ← Back
            </Button>
            <Button
              type="button"
              variant="primary"
              size="lg"
              className="flex-1"
              onClick={handleNextFromBusiness}
            >
              Next: Income Bracket →
            </Button>
          </div>
        </div>
      )}

      {/* ── Step 3: Income Bracket (before TIN generation) ── */}
      {step === 3 && (
        <div className="space-y-5">
          <div>
            <p className="text-sm font-medium text-cu-text mb-1">
              Select your monthly income bracket
              <span className="text-cu-red ml-1" aria-hidden>*</span>
            </p>
            <p className="text-xs text-cu-muted mb-3">
              This may affect your tax rate depending on trade type. All traders select a
              bracket for data completeness, including fixed-fee businesses where the
              amount may not change.
            </p>
            <div className="space-y-2" role="radiogroup" aria-label="Monthly income bracket">
              {INCOME_BRACKETS.map((b) => (
                <label
                  key={b.value}
                  className="flex items-center gap-3 rounded-md border border-cu-border px-3 py-2.5 cursor-pointer hover:border-cu-red/50 has-[:checked]:border-cu-red has-[:checked]:bg-cu-red/5"
                >
                  <input
                    type="radio"
                    value={b.value}
                    className="h-4 w-4 text-cu-red focus:ring-cu-red"
                    {...register("income_bracket")}
                  />
                  <span className="text-sm text-cu-text">{b.label}</span>
                </label>
              ))}
            </div>
            {errors.income_bracket?.message && (
              <p className="text-xs text-red-600 mt-1.5">{errors.income_bracket.message}</p>
            )}
          </div>
          <div className="flex gap-3 pt-1">
            <Button
              type="button"
              variant="secondary"
              size="lg"
              className="flex-1"
              onClick={() => setStep(2)}
              disabled={isLoading}
            >
              ← Back
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="flex-1"
              isLoading={isLoading}
            >
              Register Business
            </Button>
          </div>
        </div>
      )}
    </form>
  );
}
